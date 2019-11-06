#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <stdbool.h>
#include <pthread.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <errno.h>
#include <sys/time.h>
#include <sys/epoll.h>
#include <fcntl.h>
#include <netdb.h>

#include "LPRCClientSDK.h"
#include "common.h"
#include "utf8.h"
#include "cJSON.h"

//static bool isWaitRecogn = false;
//static int iRetryRecogn = 0;
//static char gImageUnicode[10];

//单位ms
#define CLIENT_HEART_STAMP          30000   //心跳信息发送间隔
#define CLIENT_HEART_RESP_DELAY     5000    //心跳响应时间
#define TRIGGER_DELAY               500     //图像显示在屏幕上需要一定时间，所以这里需要一个延时
#define TRIGGER_RETRY_DELAY         500     //重复触发的时间间隔
#define TRIGGER_RETRY_TIMES         6       //重复触发的次数

typedef struct {
    char color[8];
    char plate[16];
} plateInfo;

typedef enum {
    CAMERA_ACTION_UNUSE = 0,
    CAMERA_ACTION_IDLE,
    CAMERA_ACTION_TRIGGER,
    CAMERA_ACTION_WAITRESULT,
    CAMERA_ACTION_HASRESULT,
} CAMERA_STATUS;

typedef struct {
    pthread_mutex_t lock;
    //与客户端链接的socket描述符 
    int socket;
    //相机的IP Port
    char IP[16];
    unsigned int Port;
    //图片对应的unicode
    char unicode[10];

    volatile bool inUse;                 //相机是否已经被客户端所占用
    long waitSeconds;               //相机上等待识别结果的时间
    unsigned int retryTimes;
    volatile CAMERA_STATUS action;  //相机的执行动作 分别是空闲，触发，等待结果，获得结果
    volatile long triggerDelay;              //触发倒计时，时间到了进行触发
    plateInfo plateInfo;

    volatile long heart;                     //心跳，如果客户端没有响应，连续n次则认为链接断开，关闭链接，并释放对应相机
    volatile unsigned int heartRespDelay;    //发送心跳信息后等待客户端返回响应的时间，如果超出时间仍没接收到响应，则关闭连接。
    volatile bool ClientIsAlive;             //客户端连接状态标志
} CameraInfo;

typedef struct CameraList {
    CameraInfo * Info;
    struct CameraList * Next;
}CameraList;

#define MAXEVENTS 64
static CameraList *camera = NULL;
static int socket_fd, epoll_fd;

static long getCurrentTime(void)
{
    //获取系统当前时间
    long ret;
    struct timeval tv;  
    
    gettimeofday(&tv, NULL);
    ret = tv.tv_sec*1000 + tv.tv_usec/1000;
    
    return ret;
}

static void DEBUG(const char *fmt, ...)
{
    va_list arg_list;
    char buf[1024] = {0};

    //time_t sec;
    //struct tm *tm;
    struct timeval tv;

    //sec = time(NULL);
    //tm  = localtime(&sec);
    gettimeofday(&tv, NULL);

    va_start(arg_list, fmt);
    vsnprintf(buf, 1024, fmt, arg_list);
    //printf("[%02d:%02d:%02d]:%s", tm->tm_hour, tm->tm_min, tm->tm_sec, buf);
    printf("[%ld:%03ld]:%s", tv.tv_sec, tv.tv_usec/1000, buf);
    va_end(arg_list);
}

static int ListInit(void)
{
    camera = (struct CameraList *)malloc(sizeof(struct CameraList));
    if (camera == NULL) {
        perror("ListInit malloc");
        return -1;
    }

    camera->Info = NULL;
    camera->Next = NULL;

    return 0;
}

static int ListAdd(char *ip, unsigned int port)
{
    CameraList *last = camera;
    CameraList *pre = camera;

    if (ip == NULL)
        return -1;

    while(last)
    {
        pre = last;
        last = last->Next;
    }

    CameraList *new = malloc(sizeof(CameraList));
    if (new == NULL) {
        perror("ListAdd malloc");
        return -1;
    }

    new->Info = malloc(sizeof(CameraInfo));
    if (new->Info == NULL) {
        perror("ListAdd malloc");
        free(new);
        return -1;
    }

    memset(new->Info, 0, sizeof(CameraInfo));
    strncpy(new->Info->IP, ip, strlen(ip));
    new->Info->Port = port;
    if (pthread_mutex_init(&new->Info->lock, NULL) != 0) {
        perror("pthread_mutex_init");
        free(new->Info);
        free(new);
        return -1;
    }

    new->Next = NULL;

    pre->Next = new;

    return 0;
}

static void ListShow(void)
{
    CameraList *last = camera;

    while(last) {
        
        if (last->Info == NULL) {
            last = last->Next;
            continue;
        }

        DEBUG("Camera info => IP:%s Port:%d", last->Info->IP, last->Info->Port);
        last = last->Next;
    }
}

# if 0
static void ListDestroyLock(void)
{
    CameraList *last = camera;

    while(last) {
        
        if (last->Info == NULL) {
            last = last->Next;
            continue;
        }

        pthread_mutex_destroy(&last->Info->lock);

        last = last->Next;
    }   
}
#endif

static void ListDestory(void)
{
    CameraList *last = camera;
    CameraList *pre = camera;
    while(last) {
        
        if (last->Info == NULL) {
            last = last->Next;
            continue;
        }

        pthread_mutex_destroy(&last->Info->lock);
        free(last->Info);

        pre = last;
        last = last->Next;

        free(pre);
    }
}

void LPRC_DataEx2CallBackHandler(CLIENT_LPRC_PLATE_RESULTEX *recResult, LDWORD dwUser)
{
    //与结构体CLIENT_LPRC_PLATE_RESULTEX中的对应元素大小一致
    char colorbuff[8] = {0};
    char platebuff[16] = {0};
    
    CameraList *last = camera;
    
    while ( last ) {
        if (last->Info == NULL) {
            last = last->Next;
            continue;
        }

        if (strcmp(last->Info->IP, recResult->chCLIENTIP) == 0) {
            
            if (recResult->pPlateImage.nLen > 0) {
                gb_to_utf8(recResult->chColor, colorbuff, 8);
                gb_to_utf8(recResult->chLicense, platebuff, 16);

                pthread_mutex_lock(&last->Info->lock);
                
                memset(&last->Info->plateInfo, 0, sizeof(last->Info->plateInfo));
                strncpy(last->Info->plateInfo.color, colorbuff, strlen(colorbuff));
                strncpy(last->Info->plateInfo.plate, platebuff, strlen(platebuff));
                last->Info->action = CAMERA_ACTION_HASRESULT;
                
                pthread_mutex_unlock(&last->Info->lock);
            }
            break;
        }

        last = last->Next;
    }
}

// 输出连接状态的回调函数
void ConnectStatus(char *chCLIENTIP, UINT Status, LDWORD dwUser)
{
    CameraList *last = camera;

    while(last) {
        if (last->Info == NULL) {
            last = last->Next;
            continue;
        }
        if (strcmp(last->Info->IP, chCLIENTIP) == 0) {
            if (Status == 0)
                DEBUG("%s connect fail!\n", last->Info->IP);
        }
        last = last->Next;
    }
}

static cJSON * getCamera(char *numstring, int socketfd)
{
    int no = 0;
    char cameraname[20];
    CameraList *last = camera;
    cJSON * root = cJSON_CreateObject();
    cJSON * cameraInfoObj;
    int num;

    if (numstring == NULL)
        return NULL;

    if (strcmp(numstring, "MAX") == 0) {
        //100 是随便选的一个大数，因为理论上相机的数量永远不会超过两位数
        num = 100;
    } else if (strcmp(numstring, "MIN") == 0) {
        num = 1;
    } else {
        num = atoi(numstring);
    }

    DEBUG("client apply %d camera\n", num);

    cJSON_AddItemToObject(root, "type", cJSON_CreateString("apply"));
    cJSON_AddItemToObject(root, "info", cameraInfoObj = cJSON_CreateObject());
    
    while(last) {
        if (last->Info == NULL) {
            last = last->Next;
            continue;
        }
        
        //if (last->Info->inUse == false) {
            cJSON * camerainfo = cJSON_CreateObject();
            cJSON_AddItemToObject(camerainfo, "ip", cJSON_CreateString(last->Info->IP));
            cJSON_AddItemToObject(camerainfo, "port", cJSON_CreateNumber(last->Info->Port));
            memset(cameraname, 0, sizeof(cameraname));
            sprintf(cameraname, "camera%d", no);
            cJSON_AddItemToObject(cameraInfoObj, cameraname, camerainfo);

            pthread_mutex_lock(&last->Info->lock);
            last->Info->socket = socketfd;
            last->Info->ClientIsAlive = true;
            last->Info->heart = getCurrentTime();
            last->Info->heartRespDelay = CLIENT_HEART_RESP_DELAY;
            last->Info->action = CAMERA_ACTION_IDLE;
            last->Info->inUse = true;
            pthread_mutex_unlock(&last->Info->lock);

            no++;
        //}

        if (no == num)
            break;
        last = last->Next;
    }

    cJSON_AddItemToObject(root, "number", cJSON_CreateNumber(no));

    return root;
}

//设置对应的相机在delay时间后进行触发
static bool cameraTriggerSet(char *cameraip, char *unicode, unsigned int delayms)
{
    if (cameraip == NULL || unicode == NULL)
        return false;

    CameraList *last = camera;

    while (last) {
        if (last->Info == NULL) {
            last = last->Next;
            continue;
        }

        if (strcmp(last->Info->IP, cameraip) == 0) {
            if (last->Info->action == CAMERA_ACTION_IDLE) {
                pthread_mutex_lock(&last->Info->lock);
                memset(last->Info->unicode, 0, sizeof(last->Info->unicode));
                strncpy(last->Info->unicode, unicode, strlen(unicode));

                last->Info->heart = getCurrentTime();
                last->Info->triggerDelay = last->Info->heart + delayms;
                last->Info->heartRespDelay = CLIENT_HEART_RESP_DELAY;
                last->Info->ClientIsAlive = true;
                last->Info->action = CAMERA_ACTION_TRIGGER;
                pthread_mutex_unlock(&last->Info->lock);
                //printf("set action CAMERA_ACTION_TRIGGER\n");
                DEBUG("Message Unicode[%s] set action CAMERA_ACTION_TRIGGER\n", last->Info->unicode);
            }
            return true;
            //break;
        }

        last = last->Next;
    }

    return false;
}

static char * genarateRespRecognMsg(CameraList *node, char * status)
{
    if (node == NULL || status == NULL)
        return NULL;

    cJSON * root = cJSON_CreateObject();
    cJSON * child = NULL;
    cJSON * result = NULL;
    char * resultstr = NULL;

    cJSON_AddItemToObject(root, "type", cJSON_CreateString("response"));
    cJSON_AddItemToObject(root, "info", child = cJSON_CreateObject());

    cJSON_AddItemToObject(child, "unicode", cJSON_CreateString(node->Info->unicode));
    cJSON_AddItemToObject(child, "cameraip", cJSON_CreateString(node->Info->IP));
    cJSON_AddItemToObject(child, "result", result = cJSON_CreateObject());
    cJSON_AddItemToObject(result, "status", cJSON_CreateString(status));
    cJSON_AddItemToObject(result, "color", cJSON_CreateString(node->Info->plateInfo.color));
    cJSON_AddItemToObject(result, "plate", cJSON_CreateString(node->Info->plateInfo.plate));

    resultstr = cJSON_Print(root);
    cJSON_Delete(root);
    
    memset(&node->Info->plateInfo, 0, sizeof(node->Info->plateInfo));
    memset(node->Info->unicode, 0, sizeof(node->Info->unicode));

    return resultstr;
}

static char * genarateHeartMsg(CameraList *node)
{
    if (node == NULL)
        return NULL;

    cJSON * root = cJSON_CreateObject();
    cJSON_AddItemToObject(root, "type", cJSON_CreateString("heart"));
    cJSON_AddItemToObject(root, "cameraip", cJSON_CreateString(node->Info->IP));

    char * resultstr = cJSON_Print(root);
    cJSON_Delete(root);

    return resultstr;
}

static void setClientAlive(char *ip)
{
    if (ip == NULL)
        return;

    CameraList *last = camera;
    while (last) {
         if (last->Info == NULL) {
             last = last->Next;
             continue;
         }

         if (strcmp(ip, last->Info->IP) == 0) {
             pthread_mutex_lock(&last->Info->lock);
             last->Info->ClientIsAlive = true;
             pthread_mutex_unlock(&last->Info->lock);
         }

         last = last->Next;
    }
}

static void socket_send(int socket, char *str)
{
    if (str == NULL)
        return;

    char buff[1024] = {0};
    int ret;

    sprintf(buff, "%s%s%s", "<MessageHead>", str, "<MessageTail>");
    ret = send(socket, buff, strlen(buff), 0);
    if (ret < 0 ) {
        perror("send");
    }
    fflush(NULL);
    //DEBUG("socket_send:%s\n", buff);
    //输入的str指针式通过cJSON_Print申请到的地址，必须使用free进行释放
    free(str);
}

static void thread_camera_trigger_handler(void * arg)
{
    long timestamp = 0;
    int willCloseFd = 0;
    bool isClosed = false;
    //1ms定时循环
    while (1) 
    {
        //获取系统当前时间
        timestamp = getCurrentTime();

        CameraList *last = camera;

        //用来关闭socket描述符
        if (willCloseFd) {
            while (last) {
                if (last->Info == NULL) {
                    last = last->Next;
                    continue;
                }

                if (willCloseFd == last->Info->socket) {
                    DEBUG("%s %d : fd[%d] client[%s] close\n", __func__, __LINE__, last->Info->socket, last->Info->IP);
                    if (isClosed == false) {
                        close(last->Info->socket);
                        isClosed = true;
                    }
                    last->Info->socket = NULL;
                    last->Info->inUse = false;
                }

                last = last->Next;
                if (last == NULL) {
                    isClosed = false;
                    willCloseFd = 0;
                }
            }
        }

        last = camera;

        //执行功能
        while (last) {
            if (last->Info == NULL) {
                last = last->Next;
                continue;
            }

            if (last->Info->inUse == false) {
                last = last->Next;
                continue;
            }

            pthread_mutex_lock(&last->Info->lock);

            switch (last->Info->action) {
                case CAMERA_ACTION_IDLE:
                    {
                        //printf("in CAMERA_ACTION_IDLE %s\n", last->Info->IP);
                        if (last->Info->heartRespDelay == 0) {
                            if (last->Info->ClientIsAlive == false) {
                                //客户端断开，进行处理 
                                //DEBUG("%s %d : client[%s] close\n", __func__, __LINE__, last->Info->IP);
                                willCloseFd = last->Info->socket;
                                //close(last->Info->socket);
                                //last->Info->socket = NULL;
                                //last->Info->inUse = false;
                                last->Info->action = CAMERA_ACTION_UNUSE;
                            } else {
                                if (( timestamp >= last->Info->heart) && ( timestamp - last->Info->heart > CLIENT_HEART_STAMP)) {
                                    char *msg = genarateHeartMsg(last);
                                    //DEBUG("CThread Send Heart %s\n", msg);
                                    if (msg) {
                                        socket_send(last->Info->socket, msg);
                                    }
                                    last->Info->heart = getCurrentTime();
                                    last->Info->heartRespDelay = CLIENT_HEART_RESP_DELAY;
                                    last->Info->ClientIsAlive = false;
                                }
                            }
                        } else {
                            last->Info->heartRespDelay--;
                        }
                    }
                    break;
                case CAMERA_ACTION_TRIGGER:
                    {
                        if (last->Info->triggerDelay <= timestamp) {
                            //时间到，进行触发
                            DEBUG("%s CAMERA_ACTION_TRIGGER\n", last->Info->unicode);
                            last->Info->action = CAMERA_ACTION_WAITRESULT;
                            last->Info->waitSeconds = timestamp;
                            last->Info->retryTimes = 0;
                            CLIENT_LPRC_SetTrigger(last->Info->IP, last->Info->Port);
                        }                       
                    }
                    break;
                case CAMERA_ACTION_WAITRESULT:
                    {
                        //等待识别结果
                        if (timestamp - last->Info->waitSeconds > TRIGGER_RETRY_DELAY) {
                            last->Info->waitSeconds = timestamp;
                            last->Info->retryTimes++; 
                            if (last->Info->retryTimes >= TRIGGER_RETRY_TIMES) {
                                DEBUG("%s timeout CAMERA_ACTION_WAITRESULT\n", last->Info->unicode);
                                char * str = genarateRespRecognMsg(last, "failed:recogn");
                                if (str) {
                                    socket_send(last->Info->socket, str);
                                }
                                last->Info->heartRespDelay = CLIENT_HEART_RESP_DELAY;
                                last->Info->action = CAMERA_ACTION_IDLE;
                            } else {
                                DEBUG("%s retry CAMERA_ACTION_WAITRESULT\n", last->Info->unicode);
                                CLIENT_LPRC_SetTrigger(last->Info->IP, last->Info->Port);    
                            }
                        }
                    }
                    break;
                case CAMERA_ACTION_HASRESULT:
                    {
                        DEBUG("%s has result CAMERA_ACTION_HASRESULT\n", last->Info->unicode);
                        char * str = genarateRespRecognMsg(last, "success");
                        if (str) {
                            socket_send(last->Info->socket, str);
                        }
                        last->Info->heartRespDelay = CLIENT_HEART_RESP_DELAY;
                        last->Info->action = CAMERA_ACTION_IDLE;
                    }
                    break;
                default:
                    break;
            }
            pthread_mutex_unlock(&last->Info->lock);

            last = last->Next;
        }
        usleep(1000); 
    }
}


static int CameraInit(void)
{
    int ret;
    int no = 0;
    CameraList *last = camera;

    CLIENT_LPRC_RegDataEx2Event((CLIENT_LPRC_DataEx2Callback) LPRC_DataEx2CallBackHandler);
    CLIENT_LPRC_RegCLIENTConnEvent ((CLIENT_LPRC_ConnectCallback) ConnectStatus);

    while(last) {
        
        if (last->Info == NULL) {
            last = last->Next;
            continue;
        }

        DEBUG("CameraInit:IP = %s Port = %d\n", last->Info->IP, last->Info->Port);

        // 初始化。（多个相机的话，需要调用多次这个接口,输入不同的IP地址）
#if 1
        ret = CLIENT_LPRC_InitSDK(last->Info->Port, NULL, 0, last->Info->IP, no);
        if (ret == 1)
        {
            DEBUG("%s InitSDK fail\n\tthen quit\r\n", last->Info->IP);
            CLIENT_LPRC_QuitSDK();
            return -1;
        } else {
            DEBUG("%s InitSDK success\n", last->Info->IP);
        }
#endif
        last = last->Next;
        no++;
    }

    return 0;
}

/* epoll example */
static int make_socket_non_blocking(int socket_fd)
{
    int flags, s;

    flags = fcntl(socket_fd, F_GETFL, 0);
    if (flags == -1) {
        perror("fcntl");
        return -1;
    }

    flags |= O_NONBLOCK;
    s = fcntl(socket_fd, F_SETFL, flags);
    if (s == -1) {
        perror("fcntl");
        return -1;
    }

    return 0;
}

static int socket_create_bind_local(int port)
{
    struct sockaddr_in server_addr;
    int opt = 1;

    if ((socket_fd = socket(AF_INET, SOCK_STREAM, 0)) == -1) {
        perror("Socket");
        exit(1);
    }

    if (setsockopt(socket_fd,SOL_SOCKET,SO_REUSEADDR,&opt,sizeof(int)) == -1) {
        perror("Setsockopt");
        exit(1);
    }

    server_addr.sin_family = AF_INET;        
    server_addr.sin_port = htons(port);    
    server_addr.sin_addr.s_addr = INADDR_ANY;
    bzero(&(server_addr.sin_zero),8);

    if (bind(socket_fd, (struct sockaddr *)&server_addr, sizeof(struct sockaddr)) == -1) {
        perror("Unable to bind");
        return -1;
    }

    return 0;
}

static void accept_and_add_new()
{
	struct epoll_event event;
	struct sockaddr in_addr;
	socklen_t in_len = sizeof(in_addr);
	int infd;
	char hbuf[NI_MAXHOST], sbuf[NI_MAXSERV];

	while ((infd = accept(socket_fd, &in_addr, &in_len)) != -1) {

		if (getnameinfo(&in_addr, in_len,
                hbuf, sizeof(hbuf),
				sbuf, sizeof(sbuf),
				NI_NUMERICHOST | NI_NUMERICHOST) == 0) {
			DEBUG("Accepted connection on descriptor %d (host=%s, port=%s)\n",
					infd, hbuf, sbuf);
		}
		/* Make the incoming socket non-block
		 * and add it to list of fds to
		 * monitor*/
		if (make_socket_non_blocking(infd) == -1) {
			abort();
		}

		event.data.fd = infd;
		event.events = EPOLLIN | EPOLLET;
		if (epoll_ctl(epoll_fd, EPOLL_CTL_ADD, infd, &event) == -1) {
			perror("epoll_ctl");
			abort();
		}
		in_len = sizeof(in_addr);
	}

	if (errno != EAGAIN && errno != EWOULDBLOCK) {
		perror("accept");
    }
	/* else
	 *
	 * We hae processed all incomming connectioins
	 *
	 */
}

static void process_new_data(int fd)
{
	ssize_t count;
	char recvbuff[1024];

	while ((count = read(fd, recvbuff, sizeof(recvbuff) - 1))) {
		if (count == -1) {
			/* EAGAIN, read all data */
			if (errno == EAGAIN)
				return;

			perror("read");
			break;
		}

		/* Write buffer to stdout */
		recvbuff[count] = '\0';

        /* json analyse*/
        cJSON *root = cJSON_Parse(recvbuff);

        if (cJSON_HasObjectItem(root, "type")) {
            cJSON *msg = cJSON_GetObjectItem(root, "type");
            if (strcmp(msg->valuestring, "apply") == 0) {
                /*{
                  "type":"apply",
                  "number":"MAX", //or "MIN"
                  }*/
		        DEBUG("CThread Recv[%d]:%s \n", __LINE__, recvbuff);
                cJSON *num = cJSON_GetObjectItem(root, "number");
                cJSON *result = getCamera(num->valuestring, fd);
                if ( result) {
                    char * send_string = cJSON_Print(result);

                    //因为apply功能只有在启动初始化的时候被调用一次
                    //所以不需要考虑竞争
                    socket_send(fd, send_string);
                    cJSON_Delete(result);
                }
            } else if (strcmp(msg->valuestring, "request") == 0) {
                //申请进行相机触发识别
                /*{
                  "type" : "request",
                  "info" : {
                  "unicode" : "",
                  "cameraip" : "",
                  }
                  }*/
		        DEBUG("CThread Recv[%d]:%s \n", __LINE__, recvbuff);
                cJSON* info = cJSON_GetObjectItem(root, "info");
                if (cJSON_HasObjectItem(info, "unicode") && (cJSON_HasObjectItem(info, "cameraip"))) {
                    cJSON *unicode = cJSON_GetObjectItem(info, "unicode");
                    cJSON *ip = cJSON_GetObjectItem(info, "cameraip");
                    DEBUG("cameraTriggerSet cameraip=%s,unicode=%s\n", ip->valuestring, unicode->valuestring);
                    if (cameraTriggerSet(ip->valuestring, unicode->valuestring, TRIGGER_DELAY) == false) {
                        //应该发送错误信息给socketClient  
                    }
                }

            } else if (strcmp(msg->valuestring, "heart") == 0) {
                //printf("recv heart message\n");
                /*{
                  "type":"heart",
                  "cameraip":'',
                  }*/
                cJSON *cameraip = cJSON_GetObjectItem(root, "cameraip");
                setClientAlive(cameraip->valuestring);
            } else {

            }
        }

        cJSON_Delete(root);
	}
	
	DEBUG("Close connection on descriptor: %d\n", fd);
	close(fd);
}

int main(int argc, char **argv)
{
    int CameraCount;
    struct epoll_event event;
    struct epoll_event *events;
    int port;

    if (argc < 4) {
        DEBUG("paramter too low!\n");
        return -1;
    }

    ListInit();

    /*从参数列表读取参数*/
    port = atoi(argv[1]);
    DEBUG("local socket port:%d\n", port);

    CameraCount = atoi(argv[2]);

    for (int i = 0; i < CameraCount; i++) {
        DEBUG("add list %d\n", i);
        ListAdd(argv[3+(2*i)], atoi(argv[4+(2*i)]));
    }

    ListShow();

    socket_create_bind_local(port);

    if (make_socket_non_blocking(socket_fd) == -1)
        exit(1);

    if (listen(socket_fd, 10) == -1) {
        perror("Listen");
        exit(1);
    }

    epoll_fd = epoll_create1(0);
    if (epoll_fd == -1) {
        perror("epoll_create1");
        exit(1);
    }

    event.data.fd = socket_fd;
    event.events = EPOLLIN | EPOLLET;
    if (epoll_ctl(epoll_fd, EPOLL_CTL_ADD, socket_fd, &event) == -1) {
        perror("epoll_ctl");
        exit(1);
    }

    events = calloc(MAXEVENTS, sizeof(event));

    //注册相机sdk的相关功能
    //注册获取识别结果数据的回调函数
    if (CameraInit() < 0) {
        ListDestory();
        return -1;
    }

    //处理识别信息的线程
    pthread_t pthread_id;
    if (pthread_create(&pthread_id, NULL, (void *)&thread_camera_trigger_handler, 0) == -1) {
        perror("pthread_create");
        return -1;
    }

    while(1)
    {
        int n, i;
        n = epoll_wait(epoll_fd, events, MAXEVENTS, -1);
        for (i = 0; i < n; i++) {
            if (events[i].events & EPOLLERR || events[i].events & EPOLLHUP ||
                    !(events[i].events & EPOLLIN)) {
                /* An error on this fd or socket not ready */
                perror("epoll error");
                close(events[i].data.fd);
            } else if (events[i].data.fd == socket_fd) {
                /* New incoming connection */
                accept_and_add_new();
            } else {
                /* Data incoming on fd */
                process_new_data(events[i].data.fd);
            }
        }
    }

    pthread_join(pthread_id, NULL);
    //ListDestroyLock();

    free(events);
    close(socket_fd);
    // 释放资源
    CLIENT_LPRC_QuitSDK();
    ListDestory();

    return 0;
}

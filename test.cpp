#include <iostream>
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <errno.h>
#include <pthread.h>
#include "LPRCClientSDK.h"

using namespace std;

class Park {
    private:
        int server_fd;
        sockaddr_in server_addr;
        int CAMERA_PORT = 8080;
        const char *pstrCameraIN_ip = (char *)"192.168.200.251";
    
    public:
        char * chPath = "./";

    public:
        Park(){}
        ~Park(){}

        void setPicturePath(char * dir) {
            strncpy(chPath, dir, strlen(dir));
        }

        int SocketInit(void) {
            memset(&server_addr, 0, sizeof(server_addr));
            server_addr.sin_family = AF_INIT;
            server_addr.sin_addr.s_addr = inet_addr("127.0.0.1");
            server_addr.sin_port = htons(9876);
            server_fd = socket(PF_INET, SOCK_STREAM, 0);
            if (connect(server_fd, (struct sockaddr *)&server_addr, sizeof(struct sockaddr)) < 0) {
                perror("connect");
                return -1;
            }
            return 0;
        }

        int CameraInit(const char *camera_ip, int camera_port)
        {
            // 注册获取识别结果数据的回调函数
            int ret;
            CLIENT_LPRC_RegDataEx2Event((CLIENT_LPRC_DataEx2Callback) &Park::LPRC_DataEx2CallBackHandler);
            // 注册链接状态的回调函数
            CLIENT_LPRC_RegCLIENTConnEvent ((CLIENT_LPRC_ConnectCallback) &Park::ConnectStatus);
            // 设置图片保存的路径（设置路径后，接口库会自动将识别结果保存到指定目录下）
            CLIENT_LPRC_SetSavePath(chPath);
            // 初始化。（多个相机的话，需要调用多次这个接口,输入不同的IP地址）
            ret =  CLIENT_LPRC_InitSDK(camera_port, NULL, 0, camera_ip, 1);
            if (ret == 1)
            {
                printf("%s InitSDK fail\n\tthen quit\r\n", camera_ip);
                CLIENT_LPRC_QuitSDK();
                return -1;
            } else {
                printf("%s InitSDK success\n", camera_ip);
                return 0;
            }
        }

        void LPRC_DataEx2CallBackHandler(CLIENT_LPRC_PLATE_RESULTEX *recResult, LDWORD dwUser) {}
        void ConnectStatus(char *chCLIENTIP, UINT Status, LDWORD dwUser) {}
};


int main()
{
    cout << "Hello, world!" << endl;
    return 0;
}

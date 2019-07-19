#ifndef _CLIENT_H
#define _CLIENT_H

#if !defined(WIN32) && !defined(__stdcall)
#define __stdcall
#endif

#ifndef WIN32
typedef unsigned int UINT;
typedef void *HWND;
#endif
typedef unsigned long LDWORD; 
#ifdef __cplusplus
extern "C" {
#endif
#define CLIENT_LPRC_BIG_PICSTREAM_SIZE     200000-312		/*相机上传jpeg流每帧占用的内存的最大大小*/
#define CLIENT_LPRC_BIG_PICSTREAM_SIZE_EX   1*800*1024-312	/*相机上传全景图占用内存的最大大小		*/
#define CLIENT_LPRC_SMALL_PICSTREAM_SIZE_EX   10000			/*相机上传车牌截图占用内存的最大大小	*/

/* 相机时间 */
typedef struct 
{
	int Year;			/* 年 	*/
	int Month;			/* 月 	*/
	int Day;			/* 日 	*/
	int Hour;			/* 时 	*/
	int Minute;			/* 分 	*/
	int Second;			/* 秒 	*/
	int Millisecond;	/* 微妙 */
}CLIENT_LPRC_CAMERA_TIME;

/* 识别结果坐标 */
typedef struct 
{
	int 	Left;	/* 左 */
	int 	Top;	/* 上 */
	int 	Right;	/* 右 */
	int 	Bottom;	/* 下 */
}CLIENT_LPRC_PLATE_LOCATION;
/* 图像信息*/
typedef struct
{
	int				nWidth;							/* 宽度					*/
	int				nHeight;						/* 高度					*/
	int				nPitch;							/* 图像宽度的一行像素所占内存字节数*/
	int				nLen;							/* 图像的长度			*/
	char			reserved[16];					/* 预留     			*/
	unsigned char	*pBuffer;						/* 图像内存的首地址		*/
}CLIENT_LPRC_IMAGE_INFO;

/* 识别结果 */
typedef struct 
{	
	char				chCLIENTIP[16];						/* 相机IP 				*/
	char				chColor[8];							/* 车牌颜色 			*/
	char				chLicense[16];						/* 车牌号码 			*/
	CLIENT_LPRC_PLATE_LOCATION 		pcLocation;							/* 车牌在图像中的坐标 	*/
	CLIENT_LPRC_CAMERA_TIME			shootTime;							/* 识别出车牌的时间 	*/
	int					nConfidence;						/* 车牌可信度			*/
	int					nTime;								/* 识别耗时				*/
	int					nDirection;							/* 车牌方向		    	*/
	char				reserved[256];						/* 预留     			*/
	CLIENT_LPRC_IMAGE_INFO		pFullImage;						/* 全景图像数据(注意：相机不传输，此处指针为空) */
	CLIENT_LPRC_IMAGE_INFO		pPlateImage;						/* 车牌图像数据(注意：相机不传输，此处指针为空) */
}CLIENT_LPRC_PLATE_RESULTEX;

/* Jpeg流回调返回每一帧jpeg数据结构体 */
typedef struct 
{
	char			chIp[16];				/*相机IP												*/
	char			*pchBuf;				/*每一帧jpeg数据缓冲区									*/
	unsigned int	nLen;					/*当前jpeg帧的数据长度									*/
	int				nStatus;				/* 当前jpeg帧接收状态： 0-正常, 非0-不正常 				*/
	char			reserved[128];			/* 保留		  											*/
}CLIENT_LPRC_DEVDATA_INFO;
/*接收串口数据的结构体*/
typedef struct
{
	unsigned char *pData;					/*串口数据指针											*/
	int nsize;								/*串口数据大小											*/
	char reserved[128];						/* 保留													*/
}CLIENT_LPRC_DEVSERIAL_DATA;
/* 搜索设备之后保存设备信息的结构体，注:要是修改ip信息请保证其他信息不被改变*/
typedef struct 
{
	char 			chDevName[256];			/* 设备名		*/
	char			chSoftVer[20];			/* 软件版本号	*/
	char 			chHardVer[20];			/* 硬件版本号	*/
	char 			chSysVer[20];			/* 系统版本	*/
	int				nSdkPort;				/* sdk端口号			*/
	char 			chIp[16];				/* ip地址		*/
	char 			chGateway[16];			/* 网管	*/
	char 			chNetmask[16];			/* 子网掩码	*/
	char 			chMac[18];				/* Mac地址		*/
	char            chRoomID[20];				/*RooMID            */
	char            chSN[20];					/*SN*/
	char			reserved[256];			/* 保留		  */
}CLIENT_LPRC_DeviceInfo;

/*新版本Rs485透传数据结构体*/   
typedef struct{
	short           TimeDelay;	/*延时范围:10~200之间
						        注:1、设置的是本条数据和下一条数据之间的延时时间
						           2、最后一条数据不需要设置延时*/		
    unsigned char   *data;      /*存储传输数据的缓冲区指针，需要客户自己申请缓冲区*/
	short           datalen;    /*缓冲区最大长度2*1024*/
	char            reserved[10];/*保留*/
 } CLIENT_LPRC_RS485_Data_t;

/*新版本485透传结构体*/
typedef struct{
	CLIENT_LPRC_RS485_Data_t  rS485_data[5];  /*实际发送数据的结构体*/
	int                       datanum;		  /*每次发送最大支持发送5条数据*/
} CLIENT_LPRC_RS485_Transparent_t;
/*GPIO 输入口状态 结构体 */
typedef struct{ 	
	unsigned  char gpio_in0;//GPIO IN0 0低电平 1 高电平 	
	unsigned  char gpio_in1;//GPIO IN1 0低电平 1 高电平
	unsigned  char gpio_in2;//GPIO IN2 0低电平 1 高电平
	unsigned  char gpio_in3;//GPIO IN3 0低电平 1 高电平 
}CLIENT_LPRC_GPIO_In_Statue;


/************************************************************************/
/* CLIENT_LPRC_InitSDK: 连接相机												*/
/*		Parameters:														*/
/*			nPort[in]:		连接相机的端口，现默认为8080				*/
/*			hWndHandle[in]:	接收消息的窗体句柄，当为NULL时，表示无窗体  */
/*			uMsg[in]:		用户自定义消息，当hWndHandle不为NULL时，	*/
/*							检测到有新的车牌识别结果并准备好当前车牌	*/
/*							缓冲区信息后，用::PostMessage 给窗口		*/
/*							hWndHandle发送uMsg消息，其中WPARAM参数为0，	*/
/*							LPARAM参数为0								*/
/*			chServerIP[in]:	相机的IP地址								*/
/*          dwUser[in]:     用户自定义字段，主要用来回传给回调函数。    */
/*		Return Value:   int												*/
/*							0	相机连接成功							*/
/*							1	相机连接失败							*/
/*		Notice:   														*/
/*				如果采用回调的方式获取数据时，hWndHandle句柄为NULL，	*/
/*				uMsg为0，并且注册回调函数，通知有新的数据；				*/
/*				反之，在主窗口收到消息时，调用CLIENT_LPRC_GetVehicleInfoEx获取	*/
/*				数据。													*/
/************************************************************************/
int __stdcall CLIENT_LPRC_InitSDK(UINT nPort,HWND hWndHandle,UINT uMsg,char *chServerIP,LDWORD dwUser);

/************************************************************************/
/* CLIENT_LPRC_QuitSDK: 断开所有已经连接设备，释放资源							*/
/*		Parameters:														*/
/*		Return Value:   void											*/
/************************************************************************/
void  __stdcall CLIENT_LPRC_QuitSDK();


/***********************************************************************************/
/* 回调函数:循环检测并通知相机设备通讯状态的回调函数						       */
/*		Parameters:														           */
/*			chCLIENTIP[out]:		返回设备IP								           */
/*			nStatus[out]:		设备状态：0表示网络异常或设备异常；			       */
/*										  1表示网络正常，设备已连接		    	   */
/*										  2表示网络正常，设备已连接，但相机有重启  */
/*          dwUser[out]         CLIENT_InitSDK传给sdk的用户自定义字段              */
/*		Return Value:   void											           */
/***********************************************************************************/
typedef void (*CLIENT_LPRC_ConnectCallback)(char *chCLIENTIP,UINT nStatus,LDWORD dwUser);


/***********************************************************************************/
/* 回调函数:获取相机485发送的数据						       */
/*		Parameters:														           */
/*			chWTYIP[out]:		返回设备IP								           */
/*          serialData[out]          串口数据地址										*/
/*			nlen[out]				串口数据大小										*/
/*		Return Value:   void											           */
/***********************************************************************************/
typedef void (*CLIENT_LPRC_SerialDataCallback)(char *chCLIENTIP,CLIENT_LPRC_DEVSERIAL_DATA *pSerialData,LDWORD dwUser);

/***********************************************************************************/
/* 回调函数:获取相机GPIO状态						       */
/*		Parameters:														           */
/*			chWTYIP[out]:		返回设备IP								           */
/*          pGpioState[out]          串口数据地址										*/
/*		Return Value:   void											           */
/***********************************************************************************/
typedef void (*CLIENT_LPRC_GetGpioStateCallback)(char *chWTYIP,CLIENT_LPRC_GPIO_In_Statue *pGpioState);

/************************************************************************/
/* CLIENT_LPRC_RegWTYGetGpioState: 注册获取相机GPIO状态的回调函数						*/
/*		Parameters:														*/
/*			CLIENTGpioState[in]:		CLIENT_LPRC_GetGpioStateCallback类型回调函数				*/
/*		Return Value:   void											*/
/************************************************************************/
void __stdcall CLIENT_LPRC_RegWTYGetGpioState (CLIENT_LPRC_GetGpioStateCallback CLIENTGpioState);

/************************************************************************/
/* CLIENT_LPRC_RegCLIENTConnEvent: 注册相机通讯状态的回调函数						*/
/*		Parameters:														*/
/*			CLIENTConnect[in]:		CLIENT_LPRC_ConnectCallback类型回调函数				*/
/*		Return Value:   void											*/
/************************************************************************/
void __stdcall CLIENT_LPRC_RegCLIENTConnEvent (CLIENT_LPRC_ConnectCallback CLIENTConnect);


/************************************************************************/
/* CLIENT_LPRC_CheckStatus: 主动检查相机设备的通讯状态							*/
/*		Parameters:														*/
/*			chCLIENTIP[in]:		要检查的相机的IP						*/
/*		Return Value:   int												*/
/*							0	正常									*/
/*							1	网络不通								*/
/************************************************************************/
int __stdcall CLIENT_LPRC_CheckStatus (char *chCLIENTIP);

/************************************************************************/
/* 回调函数: 注册接收识别数据回调函数									*/
/*		Parameters:														*/
/*			recResult[out]:		识别结果数据							*/
/*          dwUser[out]            CLIENT_LPRC_InitSDK传给sdk的用户自定义字段              */

/*		Return Value:   void											*/
/*	Note:																*/
/*		新扩展的回调函数，方便用户接收清晰度较高或分辨率较高的JPEG图像	*/
/************************************************************************/
typedef void (*CLIENT_LPRC_DataEx2Callback)(CLIENT_LPRC_PLATE_RESULTEX *recResultEx,LDWORD dwUser);

/************************************************************************/
/* CLIENT_LPRC_RegSerialDataEvent: 注册获取串口数据的回调函数							*/
/*		Parameters:														*/
/*			CLIENTSerialData[in]:		处理接收串口数据的回调函数的指针			*/
/*		Return Value:   void											*/
/************************************************************************/
void __stdcall CLIENT_LPRC_RegSerialDataEvent(CLIENT_LPRC_SerialDataCallback CLIENTSerialData);

/************************************************************************/
/* CLIENT_LPRC_RegDataEx2Event: 注册获取识别结果的回调函数						*/
/*		Parameters:														*/
/*			CLIENTData[in]:		处理识别结果的回调函数的指针			*/
/*		Return Value:   void											*/
/*	Note:																*/
/*		接收清晰度较高，或分辨率较高的JPEG图像							*/
/************************************************************************/
void __stdcall CLIENT_LPRC_RegDataEx2Event(CLIENT_LPRC_DataEx2Callback CLIENTDataEx2);

/************************************************************************/
/* 	函数: 消息方式获取指定IP的相机识别结果。							*/
/*		  当CLIENT_LPRC_initSDK函数中设置了窗体句柄和消息时，					*/
/*		  需要在消息处理函数中调用此函数来主动获取识别结果。			*/
/*		Parameters:														*/
/*			chCLIENTIP[in]:		根据消息，获取指定IP设备识别数据		*/
/*			chPlate[in]:		车牌号码								*/
/*			chColor[in]:		车牌颜色								*/
/*			chFullImage[in]:	全景图数据								*/
/*			nFullLen[in]:		全景图数据长度							*/
/*			chPlateImage[in]:	车牌图数据								*/
/*			nPlateLen[in]:		车牌图数据长度							*/
/*		Return Value:   int												*/
/*							0	获取成功								*/
/*							1	获取失败								*/
/*		Notice:   														*/
/*			当设置了传输内容不传时，各自对应的数据为NULL，长度为-1；	*/
/*			当没有形成数据时，各自对应数据为NULL，长度为0				*/
/************************************************************************/
int __stdcall CLIENT_LPRC_GetVehicleInfoEx(char *chCLIENTIP,
								 char *chPlate,	
								 char *chColor,
								 void *chFullImage ,
								 int *nFullLen,
								 void *chPlateImage,
								 int *nPlateLen);

/************************************************************************/
/* CLIENT_LPRC_SetSavePath: 如果用户需要动态库自动保存图片，可以通过该函数设置保*/
/*					存图片的路径。										*/
/*		Parameters:														*/
/*			chSavePath[in]:	文件存储路径，以"\\"结束，如："D:\\Image\\"	*/
/*		Return Value:   void											*/
/*																		*/
/*		Notice:   														*/
/*			全景图：指定目录\\设备IP\\年月日（YYYYMMDD）\\FullImage\\	*/
/*									时分秒-毫秒__颜色_车牌号码__.jpg	*/
/*			车牌图：指定目录\\设备IP\\年月日（YYYYMMDD）\\PlatelImage\\	*/
/*									时分秒-毫秒__颜色_车牌号码__.jpg	*/
/************************************************************************/
void __stdcall CLIENT_LPRC_SetSavePath (char *chSavePath);


/************************************************************************/
/* CLIENT_LPRC_SetTrigger: 触发识别												*/
/*		Parameters:														*/
/*			pCameraIP[in]:			要触发的相机设备的IP				*/
/*			nCameraPort[in]:		端口,默认8080						*/
/*		Return Value:													*/
/*					0	触发成功返回									*/
/*				  非0	失败											*/
/************************************************************************/	
int __stdcall CLIENT_LPRC_SetTrigger(char *pCameraIP, int nCameraPort);


/************************************************************************/
/* CLIENT_LPRC_SetTransContent: 控制相机设备上传内容					        */
/*		Parameters:														*/
/*			pCameraIP[in]:		要设置的设备IP							*/
/*			nCameraPort[in]:	端口,默认8080							*/
/*			nFullImg[in]:		全景图，0表示不传，1表示传				*/
/*			nPlateImg[in]:		车牌图，0表示不传，1表示传				*/
/*		Return Value:   int												*/
/*							0	成功									*/
/*						  非0	失败									*/
/************************************************************************/
int __stdcall CLIENT_LPRC_SetTransContent (char *pCameraIP, int nCameraPort, int nFullImg, int nPlateImg);


/************************************************************************/
/* 函数说明: 控制继电器的闭合											*/
/*		Parameters:														*/
/*			pCameraIP[in]:			相机IP								*/
/*			nCameraPort[in]:		端口,默认8080						*/
/*		Return Value:   int												*/
/*							0	设置成功								*/
/*						  非0	失败									*/
/*		Notice:   														*/
/*				通过此功能，可以在PC端通过一体机设备，来控制道闸的抬起	*/
/*				设备继电器输出信号为：开关量信号。						*/
/************************************************************************/
int __stdcall CLIENT_LPRC_SetRelayClose(char *pCameraIP, int nCameraPort);
/************************************************************************/
/* 函数说明: 控制道闸落下											*/
/*		Parameters:														*/
/*			pCameraIP[in]:			相机IP								*/
/*			nCameraPort[in]:		端口,默认8080						*/
/*		Return Value:   int												*/
/*							0	设置成功								*/
/*						  非0	失败									*/
/*		Notice:   														*/
/*				通过此功能，可以在PC端通过一体机设备，来控制道闸的落下	*/
/*				设备继电器输出信号为：开关量信号。						*/
/************************************************************************/
int __stdcall CLIENT_LPRC_DropRod(char *pCameraIP, int nCameraPort);



/************************************************************************/
/* 回调函数: 获取Jpeg流的回调函数										*/
/*		Parameters:														*/
/*			JpegInfo[out]:		JPEG流数据信息							*/
/*          dwUser[out]            CLIENT_LPRC_InitSDK传给sdk的用户自定义字段              */

/*		Return Value:   void											*/
/*																		*/
/*		Notice:															*/
/*			1:一台PC连接多台设备时，此函数仅需实现一次。当区分不同		*/
/*			设备的JPEG流时，可以通过输出参数中CLIENT_LPRC_DEVDATA_INFO中的chIp来	*/
/*			区分.														*/
/*			2:此功能目前适用于V5.5.3.0、V6.0.0.0及以上版本,				*/
/*			  V5.2.1.0、V5.2.2.0、V5.2.6.0等版本不能使用此功能			*/
/************************************************************************/
typedef void (*CLIENT_LPRC_JpegCallback)(CLIENT_LPRC_DEVDATA_INFO *JpegInfo,LDWORD dwUser);


/************************************************************************/
/* CLIENT_LPRC_RegJpegEvent: 注册获取Jpeg流的回调函数							*/
/*		Parameters:														*/
/*			JpegInfo[in]:		CLIENT_LPRC_JpegCallback类型回调函数				*/
/*		Return Value:   void											*/
/*																		*/
/*		Notice:															*/
/*			1:一台PC连接多台设备时，此函数仅需实现一次。当区分不同		*/
/*			设备的JPEG流时，可以通过输出参数中CLIENT_LPRC_DEVDATA_INFO中的chIp来	*/
/*			区分.														*/
/*			2:此功能目前适用于V5.5.3.0、V6.0.0.0及以上版本,				*/
/*			  V5.2.1.0、V5.2.2.0、V5.2.6.0等版本不能使用此功能			*/
/************************************************************************/
void __stdcall CLIENT_LPRC_RegJpegEvent(CLIENT_LPRC_JpegCallback JpegInfo);


/************************************************************************/
/* 回调函数: 获取报警信息的回调函数										*/
/*		Parameters:														*/
/*			alarmInfo[out]:		报警信息								*/
/*          dwUser[out]            CLIENT_LPRC_InitSDK传给sdk的用户自定义字段              */

/*		Return Value:   void											*/
/*																		*/
/*		Notice:															*/
/*			一台PC连接多台设备时，此函数仅需实现一次。当区分不同设备	*/
/*			的Alarm时，可以通过输出参数中CLIENT_LPRC_DEVDATA_INFO中的chIp来区分		*/
/*																		*/
/*		Notice:															*/
/*			1:一台PC连接多台设备时，此函数仅需实现一次。当区分不同		*/
/*			设备的JPEG流时，可以通过输出参数中LPRC_CLIENT_DEVDATA_INFO中的chIp来	*/
/*			区分.														*/
/*			2:此功能目前适用于V5.5.3.0、V6.0.0.0及以上版本,				*/
/*			  V5.2.1.0、V5.2.2.0、V5.2.6.0等版本不能使用此功能			*/
/************************************************************************/
typedef void (*CLIENT_LPRC_AlarmCallback)(CLIENT_LPRC_DEVDATA_INFO *alarmInfo,LDWORD dwUser);


/************************************************************************/
/* CLIENT_LPRC_RegAlarmEvent: 注册获取报警信息的回调函数						*/
/*		Parameters:														*/
/*			AlarmInfo[in]:		CLIENT_LPRC_AlarmCallback类型回调函数			*/
/*		Return Value:   void											*/
/*																		*/
/*		Notice:															*/
/*			1:一台PC连接多台设备时，此函数仅需实现一次。当区分不同		*/
/*			设备的JPEG流时，可以通过输出参数中LPRC_CLIENT_DEVDATA_INFO中的chIp来	*/
/*			区分.														*/
/*			2:此功能目前适用于V5.5.3.0、V6.0.0.0及以上版本,				*/
/*			  V5.2.1.0、V5.2.2.0、V5.2.6.0等版本不能使用此功能			*/
/************************************************************************/

void __stdcall CLIENT_LPRC_RegAlarmEvent(CLIENT_LPRC_AlarmCallback AlarmInfo);


/************************************************************************/
/* CLIENT_LPRC_RS485Send: RS485透明传输											*/
/*		Parameters:														*/
/*			pCameraIP[in]				相机设备IP地址					*/
/*			nPort[in]					端口,默认8080					*/
/*			chData[in]					将要传输的数据块的首地址		*/
/*			nSendLen[in]				将要传输的数据块的字节数		*/
/*		Return Value:   int												*/
/*							0	成功									*/
/*						  非0	失败									*/
/*		notice：														*/
/*				1：用户通过此接口，往相机发送数据，相机设备会原样将数据	*/
/*				通过RS485接口转发出去，到客户所接的外部设备上。			*/
/*				2：使用此功能前，需要在演示DEMO的设置界面上，设置相机不 */
/*				能传输识别结果(默认S485传输识别结果)。					*/
/************************************************************************/
int __stdcall CLIENT_LPRC_RS485Send(char *pCameraIP, int nCameraPort, char *chData, int nSendLen);

/************************************************************************/
/* CLIENT_LPRC_RS485SendEx: 新版本RS485透明传输											*/
/*		Parameters:														*/
/*			pCameraIP[in]				相机设备IP地址					*/
/*			nPort[in]					端口,默认9110					*/
/*			nRs485[in]	传输485数据的结构体		*/
/*		Return Value:   int												*/
/*							0	成功									*/
/*						  非0	失败									*/
/*		notice：														*/
/*				1：用户通过此接口，往相机发送数据，相机设备会原样将数据	*/
/*				通过RS485接口转发出去，到客户所接的外部设备上。			*/
/*				2：使用此功能前，需要在演示DEMO的设置界面上，设置相机不 */
/*				能传输识别结果(默认S485传输识别结果)。					*/
/*				3:新版本可以一次性给相机发送最大5条数据，可以设置每条数据*/
/*				透传的时间间隔。									      */
/************************************************************************/
int __stdcall CLIENT_LPRC_RS485SendEx(char *pCameraIP, int nCameraPort, CLIENT_LPRC_RS485_Transparent_t nRs485);


/************************************************************************/
/* 函数: Jpeg流消息处理初始化											*/
/*		Parameters:														*/
/*			hWndHandle[in]:	接收消息的窗体句柄							*/
/*			uMsg[in]:		用户自定义消息								*/
/*							检测到有数据并准备好缓冲区数据后，			*/
/*							用::PostMessage 给窗口hWndHandle发送uMsg	*/
/*							消息，其中WPARAM参数为0，LPARAM参数为0		*/
/*			chIp[in]:		相机IP地址								*/
/*		Return Value:   int												*/
/*							0	获取成功								*/
/*							1	获取失败								*/
/************************************************************************/
int __stdcall CLIENT_LPRC_JpegMessageInit(HWND hWndHandle,UINT uMsg,char *chIp);


/************************************************************************/
/* 	函数: 消息方式获取指定IP的相机的Jpeg流数据							*/
/*		Parameters:														*/
/*			chIp[in]:			相机IP地址								*/
/*			chJpegBuf[in]:		存储JPEG的buffer						*/
/*			nJpegBufLen[in]:	获取到的JPEG数据长度					*/
/*		Return Value:   int												*/
/*							0	获取成功								*/
/*							1	获取失败								*/
/*		Notice:   														*/
/*			使用此函数前需先调用CLIENT_JpegMessageInit函数设置自定义消息	*/
/************************************************************************/
int __stdcall CLIENT_LPRC_GetJpegStream(char *chIp, char *chJpegBuf, char *nJpegBufLen);


/************************************************************************/
/* 	函数: 根据IP地址，断开指定设备链接									*/
/*		Parameters:														*/
/*			pCameraIP[in]:			相机IP地址							*/
/*		Return Value:   int												*/
/*							0	获取成功								*/
/*							1	获取失败								*/
/************************************************************************/
int __stdcall CLIENT_LPRC_QuitDevice(char *pCameraIP);


/************************************************************************/
/* CLIENT_LPRC_SetNetworkCardBind: 手动绑定指定网卡IP							*/
/*		Parameters:														*/
/*			pCameraIP[in]		要绑定的网卡IP地址						*/
/*		Return Value:   int												*/
/*							0	成功									*/
/*						  非0	失败									*/
/*		notice:当PC机存在多网卡的情况时，又不想禁用为单网卡时，可通过该	*/
/*				函数绑定与相机通讯的网卡IP								*/
/************************************************************************/
int __stdcall CLIENT_LPRC_SetNetworkCardBind(char *pCameraIP);
/*************************************************************************/
/*CLIENT_LPRC_SnapJpegFrame 快速抓拍一帧，两种保存方式，直接保存到固定目录或者保存到特定内存,要是保存特定内存模式需要传入内存最大值,两种方式可选*/
/*		Parameters:														*/
/*			chIp[in]		   相机的IP地址						*/
/*			pSaveFileName[in]  路径和带JPEG后缀名的文件名，用于把当前抓拍到的帧保存为特定文件  默认先匹配文件名	*/
/*          pSaveBuf[in]       用于保存当前帧在特定内存的,并且需要传输内存可存储的最大值，当文件名为空的时候这个才会生效。*/  
/*          Maxlen[in]         保存当前帧特定内存的最大值*/
/*		Return Value:   int												*/
/*						   0	保存到特定目录成功									*/
/*                         >0   保存到特定内存的数据的实际大小                                            */
/*						  -1	失败									*/
/************************************************************************/
int __stdcall CLIENT_LPRC_SnapJpegFrame(char *chIp,char *pSaveFileName,unsigned char *pSaveBuf,int Maxlen);

/************************************************************************/
/* CLIENT_LPRC_SetJpegStreamPlayOrStop: 设置jpeg流的开关							    */
/*		Parameters:														*/
/*		pCameraIP[in]		需要设置的相机设备的ip地址				    */
/*		onoff[in]			jpeg流开关项，0表示关闭流，1表示打开流		*/
/*		Return Value:   	int											*/
/*							0	成功									*/
/*						  	非0	失败									*/
/************************************************************************/
int __stdcall CLIENT_LPRC_SetJpegStreamPlayOrStop(char *pCameraIP,int onoff);

/************************************************************************/
/* CLIENT_LPRC_SearchDeviceList:    搜索设备IP列表							    */
/*		Parameters:														*/
/*		pBuf[out]			存储搜索到的相机列表信息结构体数组		*/
/*		Return Value:   	int											*/
/*							大于0	成功搜索到的设备数									*/
/*						  	-1	失败									*/
/************************************************************************/
int __stdcall CLIENT_LPRC_SearchDeviceList(CLIENT_LPRC_DeviceInfo *pBuf);

/************************************************************************/
/* CLIENT_LPRC_AlterDeviceInfo:    修改指定的设备的设备信息							    */
/*		Parameters:														*/
/*		pCameraIP[in]		需要修改的相机设备的ip地址				    */
/*		pBuf[out]			存储需要修改的设备信息结构体		*/
/*		Return Value:   	int											*/
/*							==0	成功									*/
/*						  	非0	失败									*/
/************************************************************************/
int __stdcall CLIENT_LPRC_AlterDeviceInfo(char *pCameraIP,CLIENT_LPRC_DeviceInfo pBuf);

/************************************************************************/
/* CLIENT_LPRC_SetDevTimeParam:    修改设备系统时间							    */
/*		Parameters:														*/
/*		pCameraIP[in]		需要修改的相机设备的ip地址				    */
/*		sysTime[in]			设置时间结构体		*/
/*		Return Value:   	int											*/
/*							==0	成功									*/
/*						  	非0	失败									*/
/************************************************************************/

int __stdcall CLIENT_LPRC_SetDevTimeParam(char *pCameraIP, CLIENT_LPRC_CAMERA_TIME *sysTime);


#ifdef __cplusplus
}
#endif

#endif


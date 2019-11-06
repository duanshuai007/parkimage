#include <stdio.h>
#include <stdlib.h>
#include <time.h>

int main(void)
{
    time_t t;
    struct timeval tv;

    t = time(NULL);
    gettimeofday(&tv, NULL);

    printf("time= %ld\n", t);

    printf("second:%ld\n",tv.tv_sec);  //秒
    printf("millisecond:%ld\n",tv.tv_sec*1000 + tv.tv_usec/1000);  //毫秒
    printf("microsecond:%ld\n",tv.tv_sec*1000000 + tv.tv_usec);  //微秒


    sleep(3);
    gettimeofday(&tv,NULL);
    printf("second:%ld\n",tv.tv_sec);  //秒
    printf("millisecond:%ld\n",tv.tv_sec*1000 + tv.tv_usec/1000);  //毫秒
    printf("microsecond:%ld\n",tv.tv_sec*1000000 + tv.tv_usec);  //微秒

    return 0;
}

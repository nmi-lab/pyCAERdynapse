#define CAER_LOG_DEBUG "DEBUG"
#define CAER_LOG_ERROR "ERROR"
#define CAER_LOG_NOTICE "NOTICE"

typedef int caerDeviceHandle;
typedef int sshsNode;
typedef int node;
void caerLog(const char* type, const char * arg1, const char * arg2){
  printf("caerLog: %s, %s: %s \n", type, arg1, arg2) ;
}

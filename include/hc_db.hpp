#include <vector>
#include <string>
#include <sstream>
#include <iostream>

#define DB_MISC      0x0  // 0x001  // misc debug, not yet classified.
#define DB_CMD       0x1  // 0x002  // Kernel and COpy Commands and synchronization
#define DB_WAIT      0x2  // 0x004  // Synchronization and waiting for commands to finish.
#define DB_AQL       0x3  // 0x008  // Decode and display AQL packets 
#define DB_QUEUE     0x4  // 0x010  // Queue creation and desruction commands
#define DB_SIG       0x5  // 0x020  // Signal creation, allocation, pool
#define DB_LOCK      0x6  // 0x040  // Locks and HCC thread-safety code
#define DB_KERNARG   0x7  // 0x080  // Decode and display AQL packets 
#define DB_COPY      0x8  // 0x100  // Copy debug
#define DB_COPY2     0x9  // 0x200  // More detailed copy debug


static std::vector<std::string> g_DbStr = {"misc", "cmd ", "wait", "aql ", "que ", "sign", "lock", "karg", "cpy ", "cpy2"};


// Class with a constructor that gets called when new thread is created:
struct ShortTid {
    ShortTid();
    int _shortTid;
};


// Macro for prettier debug messages, use like:
// DBOUT(DB_QUEUE, "Something happened" << myId() << " i= " << i << "\n");
#define COMPILE_HCC_DB 1

#define DBFLAG(db_flag) (HCC_DB & (1<<db_flag))

// Use str::stream so output is atomic wrt other threads:
#define DBOUT(db_flag, msg) \
if (COMPILE_HCC_DB && (HCC_DB & (1<<(db_flag)))) { \
    std::stringstream sstream;\
    sstream << "   hcc-" << g_DbStr[db_flag] << " tid:" << hcc_tlsShortTid._shortTid << " " << msg ; \
    std::cerr << sstream.str();\
};

// DBOUT + newline
#define DBOUTL(db_flag, msg) \
if (COMPILE_HCC_DB && (HCC_DB & (1<<(db_flag)))) { \
    std::stringstream sstream;\
    sstream << "   hcc-" << g_DbStr[db_flag] << " tid:" << hcc_tlsShortTid._shortTid << " " << msg << "\n"; \
    std::cerr << sstream.str();\
};


extern unsigned HCC_DB;
extern thread_local ShortTid hcc_tlsShortTid;

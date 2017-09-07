//===----------------------------------------------------------------------===//
//
// This file is distributed under the University of Illinois Open Source
// License. See LICENSE.TXT for details.
//
//===----------------------------------------------------------------------===//
#include <iostream>
#include <string>
#include <cassert>
#include <cstddef>
#include <tuple>

#include "amp.h"
#include <mutex>

#include "mcwamp_impl.hpp"

#ifdef linux
  #define CPU_RUNTIME "libmcwamp_cpu.so"
	#include <dlfcn.h>
  #define LOAD_LIBRARY(LIBRARY_NAME) dlopen((LIBRARY_NAME), RTLD_LAZY|RTLD_NODELETE)
  #define LOAD_FUNCTION(LIBRARY_HANDLE, FUNC_NAME) dlsym((LIBRARY_HANDLE), (FUNC_NAME))
  #define CLOSE_LIBRARY(LIBRARY_HANDLE) dlclose((LIBRARY_HANDLE))
  #define LIBRARY_ERROR() dlerror()
#elif _WIN32
  #define CPU_RUNTIME "mcwamp_cpu.lib"
  #ifndef __GPU__
    #define NOMINMAX
    #include <windows.h>
    #define LOAD_LIBRARY(LIBRARY_NAME) LoadLibrary((LIBRARY_NAME))
    #define LOAD_FUNCTION(LIBRARY_HANDLE, FUNC_NAME) GetProcAddress((HMODULE) (LIBRARY_HANDLE), (FUNC_NAME))
    #define CLOSE_LIBRARY(LIBRARY_HANDLE) FreeLibrary((HMODULE) (LIBRARY_HANDLE))
    #define LIBRARY_ERROR() GetLastError()
  #else
    #define LOAD_LIBRARY(LIBRARY_NAME) nullptr
    #define LOAD_FUNCTION(LIBRARY_HANDLE, FUNC_NAME) nullptr
    #define CLOSE_LIBRARY(LIBRARY_HANDLE) 0
    #define LIBRARY_ERROR() 0
  #endif
#endif

#include "hc.hpp"


namespace Concurrency {

const wchar_t accelerator::cpu_accelerator[] = L"cpu";
const wchar_t accelerator::default_accelerator[] = L"default";

} // namespace Concurrency

// weak symbols of kernel codes

// Kernel bundle
extern unsigned char kernel_binary_data[];


// interface of HCC runtime implementation
struct RuntimeImpl {
  RuntimeImpl(const char* libraryName) :
    m_ImplName(libraryName),
    m_RuntimeHandle(nullptr),
    m_PushArgImpl(nullptr),
    m_PushArgPtrImpl(nullptr),
    m_GetContextImpl(nullptr),
    isCPU(false) {
    //std::cout << "dlopen(" << libraryName << ")\n";
    m_RuntimeHandle = LOAD_LIBRARY(libraryName);
    if (!m_RuntimeHandle) {
      std::cerr << "C++AMP runtime load error: " << LIBRARY_ERROR() << std::endl;
      return;
    }
    LoadSymbols();
  }

  ~RuntimeImpl() {
    if (m_RuntimeHandle) {
      CLOSE_LIBRARY(m_RuntimeHandle);
    }
  }

  // load symbols from C++AMP runtime implementation
  void LoadSymbols() {
    m_PushArgImpl = (PushArgImpl_t) LOAD_FUNCTION(m_RuntimeHandle, "PushArgImpl");
    if (!m_PushArgImpl)
      std::cout << "can't load m_PushArgImpl" << std::endl << LIBRARY_ERROR() << std::endl;
    m_PushArgPtrImpl = (PushArgPtrImpl_t) LOAD_FUNCTION(m_RuntimeHandle, "PushArgPtrImpl");
    if (!m_PushArgPtrImpl)
      std::cout << "can't load m_PushArgPtrImpl" << std::endl << LIBRARY_ERROR() << std::endl;
    m_GetContextImpl= (GetContextImpl_t) LOAD_FUNCTION(m_RuntimeHandle, "GetContextImpl");
    if (!m_GetContextImpl)
      std::cout << "can't load m_GetContextImpl" << std::endl << LIBRARY_ERROR() << std::endl;
  }

  void set_cpu() { isCPU = true; }
  bool is_cpu() const { return isCPU; }

  std::string m_ImplName;
  void* m_RuntimeHandle;
  PushArgImpl_t m_PushArgImpl;
  PushArgPtrImpl_t m_PushArgPtrImpl;
  GetContextImpl_t m_GetContextImpl;
  bool isCPU;
};

namespace Kalmar {
namespace CLAMP {

////////////////////////////////////////////////////////////
// Class declaration
////////////////////////////////////////////////////////////
/**
 * \brief Base class of platform detection
 */
class PlatformDetect {
public:
  PlatformDetect(const std::string& name,
                 const std::string& ampRuntimeLibrary,
                 void* kernel_source)
    : m_name(name),
      m_ampRuntimeLibrary(ampRuntimeLibrary),
      m_kernel_source(kernel_source) {}

  virtual bool detect() {
    //std::cout << "Detecting " << m_name << "...";
    // detect if kernel is available
    if (!m_kernel_source) {
      //std::cout << " kernel not found" << std::endl;
      return false;
    }
    //std::cout << " kernel found...";

    void* handle = nullptr;

    // detect if C++AMP runtime is available and
    // whether all platform library dependencies are satisfied
    //std::cout << "dlopen(" << m_ampRuntimeLibrary << ")\n";
	handle = LOAD_LIBRARY(m_ampRuntimeLibrary.c_str());
    if (!handle) {
      //std::cout << " C++AMP runtime not found" << std::endl;
      //std::cout << dlerror() << std::endl;
      return false;
    }
    LIBRARY_ERROR();  // clear any existing error
    //std::cout << " C++AMP runtime found" << std::endl;
    CLOSE_LIBRARY(handle);

    return true;
  }

private:
  std::string m_ampRuntimeLibrary;
  std::string m_name;
  void* m_kernel_source;
};

/**
 * \brief PAL runtime detection
 */
class PALPlatformDetect : public PlatformDetect {
public:
#ifdef _DEBUG
  PALPlatformDetect() : PlatformDetect("PAL", "mcwamp_pal_d.dll",  (char *)kernel_binary_data + sizeof(int)) {}
#else
  PALPlatformDetect() : PlatformDetect("PAL", "mcwamp_pal.dll",  (char *)kernel_binary_data + sizeof(int)) {}
#endif
};


/**
 * \brief Flag to turn on/off platform-dependent runtime messages
 */
static bool mcwamp_verbose = false;

static RuntimeImpl* LoadPALRuntime() {
  RuntimeImpl* runtimeImpl = nullptr;
  // load PAL C++AMP runtime
  if (mcwamp_verbose)
    std::cout << "Use PAL runtime" << std::endl;
#ifdef _DEBUG
  runtimeImpl = new RuntimeImpl("mcwamp_pal_d.dll");
#else
  runtimeImpl = new RuntimeImpl("mcwamp_pal.dll");
#endif
  if (!runtimeImpl->m_RuntimeHandle) {
    std::cerr << "Can't load PAL runtime!" << std::endl;
    delete runtimeImpl;
    exit(-1);
  } else {
    //std::cout << "PAL C++AMP runtime loaded" << std::endl;
  }
  return runtimeImpl;
}

static RuntimeImpl* LoadCPURuntime() {
  RuntimeImpl* runtimeImpl = nullptr;
  // load CPU runtime
  if (mcwamp_verbose)
    std::cout << "Use CPU runtime" << std::endl;
  runtimeImpl = new RuntimeImpl(CPU_RUNTIME);
  if (!runtimeImpl->m_RuntimeHandle) {
    std::cerr << "Can't load CPU runtime!" << std::endl;
    delete runtimeImpl;
    exit(-1);
  }
  return runtimeImpl;
}

RuntimeImpl* GetOrInitRuntime() {
  static RuntimeImpl* runtimeImpl = nullptr;
  if (runtimeImpl == nullptr) {
    PALPlatformDetect pal_rt;

    char* verbose_env = getenv("HCC_VERBOSE");
    if (verbose_env != nullptr) {
      if (std::string("ON") == verbose_env) {
        mcwamp_verbose = true;
      }
    }

    // force use certain C++AMP runtime from HCC_RUNTIME environment variable
    char* runtime_env = getenv("HCC_RUNTIME");
    if (runtime_env != nullptr) {
      if (std::string("PAL") == runtime_env) {
        if (pal_rt.detect()) {
          runtimeImpl = LoadPALRuntime();
        } else {
          std::cerr << "Ignore unsupported HCC_RUNTIME environment variable: " << runtime_env << std::endl;
        }
      } else if(std::string("CPU") == runtime_env) {
          // CPU runtime should be available
          runtimeImpl = LoadCPURuntime();
          runtimeImpl->set_cpu();
      } else {
        std::cerr << "Ignore unknown HCC_RUNTIME environment variable:" << runtime_env << std::endl;
      }
    }

    // If can't determined by environment variable, try detect what can be used
    if (runtimeImpl == nullptr) {
      if (pal_rt.detect()) {

        runtimeImpl = LoadPALRuntime();
      } else {
          runtimeImpl = LoadCPURuntime();
          runtimeImpl->set_cpu();
          std::cerr << "No suitable runtime detected. Fall back to CPU!" << std::endl;
      }
    }
  }
  return runtimeImpl;
}

bool is_cpu()
{
    return GetOrInitRuntime()->is_cpu();
}

static bool in_kernel = false;
bool in_cpu_kernel() { return in_kernel; }
void enter_kernel() { in_kernel = true; }
void leave_kernel() { in_kernel = false; }


/// Handler for binary files. The bundled file will have the following format
/// (all integers are stored in little-endian format):
///
/// "OFFLOAD_BUNDLER_MAGIC_STR" (ASCII encoding of the string)
///
/// NumberOfOffloadBundles (8-byte integer)
///
/// OffsetOfBundle1 (8-byte integer)
/// SizeOfBundle1 (8-byte integer)
/// NumberOfBytesInTripleOfBundle1 (8-byte integer)
/// TripleOfBundle1 (byte length defined before)
///
/// ...
///
/// OffsetOfBundleN (8-byte integer)
/// SizeOfBundleN (8-byte integer)
/// NumberOfBytesInTripleOfBundleN (8-byte integer)
/// TripleOfBundleN (byte length defined before)
///
/// Bundle1
/// ...
/// BundleN

static inline uint64_t Read8byteIntegerFromBuffer(const char *data, size_t pos) {
  uint64_t Res = 0;
  for (unsigned i = 0; i < 8; ++i) {
    Res <<= 8;
    uint64_t Char = (uint64_t)data[pos + 7 - i];
    Res |= 0xffu & Char;
  }
  return Res;
}

#define RUNTIME_ERROR(val, error_string, line) { \
  printf("### HCC RUNTIME ERROR: %s at file:%s line:%d\n", error_string, __FILE__, line); \
  exit(val); \
}

#define OFFLOAD_BUNDLER_MAGIC_STR "__CLANG_OFFLOAD_BUNDLE__"
#define OFFLOAD_BUNDLER_MAGIC_STR_LENGTH (24)
#define HCC_TRIPLE_PREFIX "hcc-amdgcn--amdhsa-"
#define HCC_TRIPLE_PREFIX_LENGTH (19)

inline void DetermineAndGetProgram(KalmarQueue* pQueue, size_t* kernel_size, void** kernel_source) {

  bool FoundCompatibleKernel = false;
  // walk through bundle header
  // get bundle file size
  size_t bundle_size = (size_t) *((int *)kernel_binary_data);

  // point to bundle file data
  const char *data = ((const char *)kernel_binary_data) + sizeof(int);
  // skip OFFLOAD_BUNDLER_MAGIC_STR
  size_t pos = 0;
  if (pos + OFFLOAD_BUNDLER_MAGIC_STR_LENGTH > bundle_size) {
    RUNTIME_ERROR(1, "Bundle size too small", __LINE__)
  }
  std::string MagicStr(data + pos, OFFLOAD_BUNDLER_MAGIC_STR_LENGTH);
  if (MagicStr.compare(OFFLOAD_BUNDLER_MAGIC_STR) != 0) {
    RUNTIME_ERROR(1, "Incorrect magic string", __LINE__)
  }
  pos += OFFLOAD_BUNDLER_MAGIC_STR_LENGTH;

  // Read number of bundles.
  if (pos + 8 > bundle_size) {
    RUNTIME_ERROR(1, "Fail to parse number of bundles", __LINE__)
  }
  uint64_t NumberOfBundles = Read8byteIntegerFromBuffer(data, pos);
  pos += 8;
  for (uint64_t i = 0; i < NumberOfBundles; ++i) {
    // Read offset.
    if (pos + 8 > bundle_size) {
      RUNTIME_ERROR(1, "Fail to parse bundle offset", __LINE__)
    }
    uint64_t Offset = Read8byteIntegerFromBuffer(data, pos);
    pos += 8;
    // Read size.
    if (pos + 8 > bundle_size) {
      RUNTIME_ERROR(1, "Fail to parse bundle size", __LINE__)
    }
    uint64_t Size = Read8byteIntegerFromBuffer(data, pos);
    pos += 8;
    // Read triple size.
    if (pos + 8 > bundle_size) {
      RUNTIME_ERROR(1, "Fail to parse triple size", __LINE__)
    }
    uint64_t TripleSize = Read8byteIntegerFromBuffer(data, pos);
    pos += 8;

    // Read triple.
    if (pos + TripleSize > bundle_size) {
      RUNTIME_ERROR(1, "Fail to parse triple", __LINE__)
    }
    std::string Triple(data + pos, TripleSize);
    pos += TripleSize;

    // only check bundles with HCC triple prefix string
    if (Triple.compare(0, HCC_TRIPLE_PREFIX_LENGTH, HCC_TRIPLE_PREFIX) == 0) {
      // use KalmarDevice::IsCompatibleKernel to check
      size_t SizeST = (size_t)Size;
      void *Content = (unsigned char *)data + Offset;
      if (pQueue->getDev()->IsCompatibleKernel((void*)SizeST, Content)) {
        *kernel_size = SizeST;
        *kernel_source = Content;
        FoundCompatibleKernel = true;
        break;
      }
    }
  }

  if (!FoundCompatibleKernel) {
    RUNTIME_ERROR(1, "Fail to find compatible kernel", __LINE__)
  }
}

void BuildProgram(KalmarQueue* pQueue) {
  size_t kernel_size = 0;
  void* kernel_source = nullptr;

  DetermineAndGetProgram(pQueue, &kernel_size, &kernel_source);
  pQueue->getDev()->BuildProgram((void*)kernel_size, kernel_source);
}

// used in parallel_for_each.h
void *CreateKernel(std::string s, KalmarQueue* pQueue) {
  return pQueue->getDev()->CreateKernel(s.c_str(), pQueue);
}

void PushArg(void *k_, int idx, size_t sz, const void *s) {
  GetOrInitRuntime()->m_PushArgImpl(k_, idx, sz, s);
}
void PushArgPtr(void *k_, int idx, size_t sz, const void *s) {
  GetOrInitRuntime()->m_PushArgPtrImpl(k_, idx, sz, s);
}

} // namespace CLAMP

KalmarContext *getContext() {
  return static_cast<KalmarContext*>(CLAMP::GetOrInitRuntime()->m_GetContextImpl());
}

// Kalmar runtime bootstrap logic
class KalmarBootstrap {
private:
  RuntimeImpl* runtime;
public:
  KalmarBootstrap() : runtime(nullptr) {
    bool to_init = true;
    char* lazyinit_env = getenv("HCC_LAZYINIT");
    if (lazyinit_env != nullptr) {
      if (std::string("ON") == lazyinit_env) {
        to_init = false;
      }
    }

    if (to_init) {
      // initialize runtime
      runtime = CLAMP::GetOrInitRuntime();

      // get context
      KalmarContext* context = static_cast<KalmarContext*>(runtime->m_GetContextImpl());
      
      const std::vector<KalmarDevice*> devices = context->getDevices();

      for (auto dev = devices.begin(); dev != devices.end(); dev++) {

        // get default queue on the default device
        std::shared_ptr<KalmarQueue> queue = (*dev)->get_default_queue();

        // build kernels on the default queue on the default device
        CLAMP::BuildProgram(queue.get());
      }
    }
  }
};

} // namespace Kalmar

extern "C" void __attribute__((constructor)) __hcc_shared_library_init() {
  // this would initialize kernels when the shared library get loaded
  static Kalmar::KalmarBootstrap boot;
}

extern "C" void __attribute__((destructor)) __hcc_shared_library_fini() {
}

// conversion routines between float and half precision
static inline std::uint32_t f32_as_u32(float f) { union { float f; std::uint32_t u; } v; v.f = f; return v.u; }
static inline float u32_as_f32(std::uint32_t u) { union { float f; std::uint32_t u; } v; v.u = u; return v.f; }
static inline int clamp_int(int i, int l, int h) { return std::min(std::max(i, l), h); }

// half � float, the f16 is in the low 16 bits of the input argument �a�
static inline float __convert_half_to_float(std::uint32_t a) noexcept {
  std::uint32_t u = ((a << 13) + 0x70000000U) & 0x8fffe000U;
  std::uint32_t v = f32_as_u32(u32_as_f32(u) * 0x1.0p+112f) + 0x38000000U;
  u = (a & 0x7fff) != 0 ? v : u;
  return u32_as_f32(u) * 0x1.0p-112f;
}

// float � half with nearest even rounding
// The lower 16 bits of the result is the bit pattern for the f16
static inline std::uint32_t __convert_float_to_half(float a) noexcept {
  std::uint32_t u = f32_as_u32(a);
  int e = static_cast<int>((u >> 23) & 0xff) - 127 + 15;
  std::uint32_t m = ((u >> 11) & 0xffe) | ((u & 0xfff) != 0);
  std::uint32_t i = 0x7c00 | (m != 0 ? 0x0200 : 0);
  std::uint32_t n = ((std::uint32_t)e << 12) | m;
  std::uint32_t s = (u >> 16) & 0x8000;
  int b = clamp_int(1-e, 0, 13);
  std::uint32_t d = (0x1000 | m) >> b;
  d |= (d << b) != (0x1000 | m);
  std::uint32_t v = e < 1 ? d : n;
  v = (v >> 2) + (((v & 0x7) == 3) | ((v & 0x7) > 5));
  v = e > 30 ? 0x7c00 : v;
  v = e == 143 ? i : v;
  return s | v;
}

extern "C" float __gnu_h2f_ieee(unsigned short h){
  return __convert_half_to_float((std::uint32_t) h);
}

extern "C" unsigned short __gnu_f2h_ieee(float f){
  return (unsigned short)__convert_float_to_half(f);
}


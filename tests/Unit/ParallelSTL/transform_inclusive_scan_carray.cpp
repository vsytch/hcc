// XFAIL: Linux
// RUN: %hc %s -o %t.out && %t.out

// Parallel STL headers
#include <coordinate>
#include <experimental/algorithm>
#include <experimental/numeric>
#include <experimental/execution_policy>

// C++ headers
#include <iostream>
#include <iomanip>
#include <numeric>
#include <algorithm>
#include <iterator>

#define ROW (2)
#define COL (8)
#define TEST_SIZE (ROW * COL)

#define _DEBUG (0)

template<typename _Tp, size_t SIZE>
bool test() {
  bool ret = true;

  _Tp input[SIZE] { 0 };
  _Tp output[SIZE] { 0 };

  // initialize test data
  std::iota(std::begin(input), std::end(input), 1);

  // launch kernel with parallel STL transform inclusive scan
  using namespace std::experimental::parallel;
  transform_inclusive_scan(par, std::begin(input), std::end(input), std::begin(output), std::negate<_Tp>(), std::plus<_Tp>(), _Tp{});

  // verify data
  if (output[0] != -input[0])
    ret = false;

  for (int i = 1; i < SIZE; ++i) {
    if (output[i] != output[i - 1] - input[i]) {
      ret = false;
      break;
    }
  }

#if _DEBUG 
  for (int i = 0; i < ROW; ++i) {
    for (int j = 0; j < COL; ++j) {
      std::cout << std::setw(5) << output[i * COL + j];
    }
    std::cout << "\n";
  } 
#endif

  return ret;
}

int main() {
  bool ret = true;

  ret &= test<int, TEST_SIZE>();
  ret &= test<unsigned, TEST_SIZE>();
  ret &= test<float, TEST_SIZE>();
  ret &= test<double, TEST_SIZE>();

  return !(ret == true);
}


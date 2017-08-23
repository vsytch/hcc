#include <iostream>
#include <iomanip>
#include <fstream>
#include <functional>
#include <sstream>
#include <string>

int main(int argc, char **argv)
{
    std::ifstream kernel_bin;
    std::ofstream host_source;
    std::stringstream ss;
    std::string kernel_name,
                kernel_string,
                kernel_size,
                kernel_raw;
    char c;

    if (argc != 3)
    {
        std::cerr << "Something went wrong 1" << std::endl;
        return 1;
    }

    kernel_bin.open(argv[1], std::ifstream::in | std::ifstream::binary);
    if (kernel_bin.fail())
    {
        std::cerr << "Something went wrong 2" << std::endl;
        return 1;
    }

    host_source.open(argv[2], std::ostream::out | std::ostream::app);
    if (host_source.fail())
    {
        std::cerr << "Something went wrong 3" << std::endl;
        return 1;
    }

    host_source << "char kernel_binary_data[] = {'";

    kernel_raw = "";
    ss << std::right << std::setfill('0');
    while (kernel_bin.get(c))
    {
        ss << "\',\'\\x" << std::setw(2) << std::hex << std::uppercase << (short)(unsigned char) c;
        kernel_raw += c;
    }
    ss >> kernel_string;

    std::stringstream().swap(ss);
    ss << std::setw(2 * sizeof(int)) << std::right << std::setfill('0') << std::hex << (int) kernel_raw.size();
    ss >> kernel_size;

    for (int i = sizeof(int) - 1; i >= 0; i--)
    {
        if (i != sizeof(int) - 1)
            host_source << "\',\'";
        host_source << "\\x" << kernel_size[2 * i] << kernel_size[(2 * i) + 1];
    }
    host_source << kernel_string << "'};";

    kernel_bin.close();
    host_source.close();

    return 0;
}

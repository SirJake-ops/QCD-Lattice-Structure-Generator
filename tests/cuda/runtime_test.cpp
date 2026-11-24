//
// Created by jake on 11/23/26.
//

#include <cstring>
#include <cuda_runtime.h>
#include <iostream>

#include "gtest/gtest.h"


cudaError_t runtime_properties_helper(int device, char *buffer, std::size_t capacity) {
    cudaDeviceProp props{};
    auto err = cudaGetDeviceProperties(&props, device);

    if (err != cudaSuccess) {
        std::cerr << cudaGetErrorString(err) << std::endl;
    }

    int written = std::snprintf(buffer, capacity, "GPU: %s, compute capability: %d%d",
                                props.name, props.major, props.minor
    );
    return (written < 0 || static_cast<std::size_t>(written) >= capacity)
               ? cudaErrorInvalidValue
               : cudaSuccess;
}

namespace {
    TEST(CudaRuntimeTest, RuntimeDeviceInfoTest) {
        int count = 0;
        ASSERT_EQ(cudaGetDeviceCount(&count), cudaSuccess);
        if (count == 0) {
            GTEST_SKIP() << "No CUDA device available";
        }

        char buffer[256]{};
        ASSERT_EQ(runtime_properties_helper(0, buffer, sizeof(buffer)), cudaSuccess);

        EXPECT_NE(buffer[0], '\0');
        EXPECT_NE(std::string(buffer).find("GPU: "), std::string::npos);
        EXPECT_NE(std::string(buffer).find("compute capability: "),
                  std::string::npos);
    }
}

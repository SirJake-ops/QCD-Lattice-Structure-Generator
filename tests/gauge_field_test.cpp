#include <qcd/gauge_field.h>

#include <complex>

#include <gtest/gtest.h>

TEST(GaugeFieldMatrixTest, SupportsComplexMatrixOperations) {
    using gauge_field::Su3Matrix;
    const std::complex<double> i{0.0, 1.0};
    Su3Matrix matrix = Su3Matrix::Zero();
    matrix(0, 1) = i;
    matrix(1, 0) = 2.0;
    matrix(2, 2) = 3.0;

    Su3Matrix expected = Su3Matrix::Zero();
    expected(0, 0) = 2.0 * i;
    expected(1, 1) = 2.0 * i;
    expected(2, 2) = 9.0;
    const Su3Matrix product = matrix * matrix;
    EXPECT_TRUE(product.isApprox(expected));
    EXPECT_TRUE((matrix * Su3Matrix::Identity()).isApprox(matrix));

    const Su3Matrix adjoint = matrix.adjoint();
    EXPECT_EQ(adjoint(1, 0), -i);
    EXPECT_EQ(adjoint(0, 1), std::complex<double>(2.0, 0.0));
}

#include <qcd/statistics.h>

#include <cmath>
#include <stdexcept>

#include <gtest/gtest.h>

namespace {

TEST(RunningStatisticsTest, ComputesOnlineMoments) {
    qcd::statistics::RunningStatistics statistics;
    for (const double value : {1.0, 2.0, 3.0, 4.0}) {
        statistics.add(value);
    }

    EXPECT_EQ(statistics.count(), 4U);
    EXPECT_FALSE(statistics.empty());
    EXPECT_DOUBLE_EQ(statistics.mean(), 2.5);
    EXPECT_DOUBLE_EQ(statistics.population_variance(), 1.25);
    EXPECT_NEAR(statistics.sample_variance(), 5.0 / 3.0, 1e-15);
    EXPECT_NEAR(statistics.standard_error(), std::sqrt(5.0 / 12.0), 1e-15);
}

TEST(RunningStatisticsTest, MergesPartialAccumulators) {
    qcd::statistics::RunningStatistics first;
    qcd::statistics::RunningStatistics second;
    qcd::statistics::RunningStatistics all;

    for (const double value : {1.0, 2.0}) {
        first.add(value);
        all.add(value);
    }
    for (const double value : {3.0, 4.0}) {
        second.add(value);
        all.add(value);
    }
    first.merge(second);

    EXPECT_EQ(first.count(), all.count());
    EXPECT_DOUBLE_EQ(first.mean(), all.mean());
    EXPECT_DOUBLE_EQ(first.sample_variance(), all.sample_variance());
}

TEST(RunningStatisticsTest, IsStableForLargeOffsets) {
    qcd::statistics::RunningStatistics statistics;
    statistics.add(1'000'000'000.0 + 1.0);
    statistics.add(1'000'000'000.0 + 2.0);
    statistics.add(1'000'000'000.0 + 3.0);

    EXPECT_DOUBLE_EQ(statistics.mean(), 1'000'000'002.0);
    EXPECT_DOUBLE_EQ(statistics.sample_variance(), 1.0);
}

TEST(RunningStatisticsTest, RejectsUnderspecifiedQueries) {
    qcd::statistics::RunningStatistics statistics;
    EXPECT_TRUE(statistics.empty());
    EXPECT_THROW(static_cast<void>(statistics.mean()), std::logic_error);
    EXPECT_THROW(static_cast<void>(statistics.population_variance()), std::logic_error);
    EXPECT_THROW(static_cast<void>(statistics.sample_variance()), std::logic_error);
    EXPECT_THROW(static_cast<void>(statistics.standard_error()), std::logic_error);

    statistics.add(1.0);
    EXPECT_DOUBLE_EQ(statistics.population_variance(), 0.0);
    EXPECT_THROW(static_cast<void>(statistics.sample_variance()), std::logic_error);
}

} // namespace

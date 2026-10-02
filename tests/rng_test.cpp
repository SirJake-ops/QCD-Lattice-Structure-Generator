#include <qcd/rng.h>

#include <stdexcept>

#include <gtest/gtest.h>

namespace {

TEST(RandomStreamTest, RepeatsASequenceForTheSameSeed) {
    qcd::rng::RandomStream first(12345);
    qcd::rng::RandomStream second(12345);

    for (int draw = 0; draw < 32; ++draw) {
        EXPECT_EQ(first.next_u64(), second.next_u64());
    }
}

TEST(RandomStreamTest, DerivesStableDistinctStreams) {
    EXPECT_EQ(qcd::rng::derive_seed(42, 7), qcd::rng::derive_seed(42, 7));
    EXPECT_NE(qcd::rng::derive_seed(42, 7), qcd::rng::derive_seed(42, 8));

    qcd::rng::RandomStream first(42, 7);
    qcd::rng::RandomStream second(42, 8);
    EXPECT_NE(first.seed(), second.seed());
    EXPECT_NE(first.next_u64(), second.next_u64());
}

TEST(RandomStreamTest, GeneratesValuesWithinRequestedRanges) {
    qcd::rng::RandomStream stream(99);

    for (int draw = 0; draw < 1'000; ++draw) {
        const double unit_value = stream.uniform_unit();
        EXPECT_GE(unit_value, 0.0);
        EXPECT_LT(unit_value, 1.0);
        EXPECT_LT(stream.uniform_index(7), 7U);
    }
    EXPECT_EQ(stream.uniform_index(1), 0U);
    EXPECT_THROW(static_cast<void>(stream.uniform_index(0)), std::invalid_argument);
}

} // namespace

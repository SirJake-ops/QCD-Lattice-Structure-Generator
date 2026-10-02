#include <qcd/lattice.h>

#include <array>
#include <limits>
#include <stdexcept>
#include <vector>

#include <gtest/gtest.h>

namespace {

TEST(LatticeTest, DescribesShapeAndStorage) {
    const lattice::Lattice shape({2, 3});

    EXPECT_EQ(shape.dimension_count(), 2U);
    EXPECT_EQ(shape.extent(0), 2U);
    EXPECT_EQ(shape.extent(1), 3U);
    EXPECT_EQ(shape.volume(), 6U);
    EXPECT_EQ(shape.link_count(), 12U);
    EXPECT_EQ(std::vector(shape.extents().begin(), shape.extents().end()),
              (std::vector<std::size_t>{2, 3}));
}

TEST(LatticeTest, ConvertsCoordinatesAndIndicesRoundTrip) {
    const lattice::Lattice shape({2, 2, 2, 4});

    for (std::size_t site = 0; site < shape.volume(); ++site) {
        const auto coordinates = shape.coordinate(site);
        EXPECT_EQ(shape.site_index(coordinates), site);
    }

    EXPECT_EQ(shape.site_index(std::array<std::size_t, 4>{1, 0, 1, 3}), 29U);
}

TEST(LatticeTest, WrapsPeriodicNeighbors) {
    const lattice::Lattice shape({2, 3});
    const auto site = shape.site_index(std::array<std::size_t, 2>{1, 2});

    EXPECT_EQ(site, 5U);
    EXPECT_EQ(shape.forward_neighbor(site, 0), 4U);
    EXPECT_EQ(shape.backward_neighbor(site, 0), 4U);
    EXPECT_EQ(shape.forward_neighbor(site, 1), 1U);
    EXPECT_EQ(shape.backward_neighbor(site, 1), 3U);

    for (std::size_t direction = 0; direction < shape.dimension_count(); ++direction) {
        for (std::size_t current = 0; current < shape.volume(); ++current) {
            EXPECT_EQ(
                shape.backward_neighbor(shape.forward_neighbor(current, direction), direction),
                current);
            EXPECT_EQ(
                shape.forward_neighbor(shape.backward_neighbor(current, direction), direction),
                current);
        }
    }
}

TEST(LatticeTest, HandlesUnitExtents) {
    const lattice::Lattice shape({1, 3});

    for (std::size_t site = 0; site < shape.volume(); ++site) {
        EXPECT_EQ(shape.forward_neighbor(site, 0), site);
        EXPECT_EQ(shape.backward_neighbor(site, 0), site);
    }
}

TEST(LatticeTest, FlattensSiteDirectionPairs) {
    const lattice::Lattice shape({2, 3});

    EXPECT_EQ(shape.link_index(0, 0), 0U);
    EXPECT_EQ(shape.link_index(0, 1), 1U);
    EXPECT_EQ(shape.link_index(5, 1), 11U);
}

TEST(LatticeTest, RejectsInvalidShapesAndLocations) {
    EXPECT_THROW(lattice::Lattice({}), std::invalid_argument);
    EXPECT_THROW(lattice::Lattice({2, 0, 3}), std::invalid_argument);
    EXPECT_THROW(lattice::Lattice({std::numeric_limits<std::size_t>::max(), 2}),
                 std::overflow_error);
    EXPECT_THROW(lattice::Lattice({std::numeric_limits<std::size_t>::max() / 2 + 1, 1}),
                 std::overflow_error);

    const lattice::Lattice shape({2, 3});
    EXPECT_THROW(static_cast<void>(shape.extent(2)), std::out_of_range);
    EXPECT_THROW(static_cast<void>(shape.coordinate(6)), std::out_of_range);
    EXPECT_THROW(static_cast<void>(shape.site_index(std::array<std::size_t, 1>{0})),
                 std::invalid_argument);
    EXPECT_THROW(static_cast<void>(shape.site_index(std::array<std::size_t, 2>{2, 0})),
                 std::out_of_range);
    EXPECT_THROW(static_cast<void>(shape.forward_neighbor(6, 0)), std::out_of_range);
    EXPECT_THROW(static_cast<void>(shape.backward_neighbor(0, 2)), std::out_of_range);
    EXPECT_THROW(static_cast<void>(shape.link_index(6, 0)), std::out_of_range);
    EXPECT_THROW(static_cast<void>(shape.link_index(0, 2)), std::out_of_range);
}

} // namespace

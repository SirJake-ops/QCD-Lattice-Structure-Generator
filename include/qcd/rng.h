#pragma once

#include <cstddef>
#include <cstdint>
#include <random>

namespace qcd::rng {

using seed_type = std::uint64_t;

[[nodiscard]] seed_type derive_seed(seed_type base_seed, seed_type stream_id) noexcept;

class RandomStream {
  public:
    explicit RandomStream(seed_type seed);
    RandomStream(seed_type base_seed, seed_type stream_id);

    [[nodiscard]] seed_type seed() const noexcept;
    [[nodiscard]] std::uint64_t next_u64();
    [[nodiscard]] double uniform_unit();
    [[nodiscard]] std::size_t uniform_index(std::size_t upper_exclusive);

  private:
    seed_type seed_{};
    std::mt19937_64 engine_;
};

} // namespace qcd::rng

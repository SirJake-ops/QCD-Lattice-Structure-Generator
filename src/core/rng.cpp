#include <qcd/rng.h>

#include <stdexcept>

namespace {

std::uint64_t splitmix64(std::uint64_t value) noexcept {
    value += 0x9e3779b97f4a7c15ULL;
    value = (value ^ (value >> 30U)) * 0xbf58476d1ce4e5b9ULL;
    value = (value ^ (value >> 27U)) * 0x94d049bb133111ebULL;
    return value ^ (value >> 31U);
}

} // namespace

qcd::rng::seed_type qcd::rng::derive_seed(const seed_type base_seed,
                                          const seed_type stream_id) noexcept {
    return splitmix64(base_seed ^ splitmix64(stream_id));
}

qcd::rng::RandomStream::RandomStream(const seed_type seed) : seed_(seed), engine_(seed) {}

qcd::rng::RandomStream::RandomStream(const seed_type base_seed, const seed_type stream_id)
    : RandomStream(derive_seed(base_seed, stream_id)) {}

qcd::rng::seed_type qcd::rng::RandomStream::seed() const noexcept { return seed_; }

std::uint64_t qcd::rng::RandomStream::next_u64() { return engine_(); }

double qcd::rng::RandomStream::uniform_unit() {
    constexpr double inverse_two_to_53 = 1.0 / 9007199254740992.0;
    return static_cast<double>(next_u64() >> 11U) * inverse_two_to_53;
}

std::size_t qcd::rng::RandomStream::uniform_index(const std::size_t upper_exclusive) {
    if (upper_exclusive == 0) {
        throw std::invalid_argument("Random index upper bound must be non-zero");
    }

    const auto bound = static_cast<std::uint64_t>(upper_exclusive);
    const std::uint64_t rejection_threshold = (std::uint64_t{0} - bound) % bound;
    std::uint64_t value{};
    do {
        value = next_u64();
    } while (value < rejection_threshold);
    return static_cast<std::size_t>(value % bound);
}

#pragma once

#include <cstddef>

namespace qcd::statistics {

class RunningStatistics {
  public:
    void add(double value) noexcept;
    void merge(const RunningStatistics &other) noexcept;

    [[nodiscard]] std::size_t count() const noexcept;
    [[nodiscard]] bool empty() const noexcept;
    [[nodiscard]] double mean() const;
    [[nodiscard]] double population_variance() const;
    [[nodiscard]] double sample_variance() const;
    [[nodiscard]] double standard_error() const;

  private:
    std::size_t count_{};
    double mean_{};
    double squared_deviation_sum_{};
};

} // namespace qcd::statistics

#include <qcd/statistics.h>

#include <cmath>
#include <stdexcept>

void qcd::statistics::RunningStatistics::add(const double value) noexcept {
    ++count_;
    const double delta = value - mean_;
    mean_ += delta / static_cast<double>(count_);
    const double adjusted_delta = value - mean_;
    squared_deviation_sum_ += delta * adjusted_delta;
}

void qcd::statistics::RunningStatistics::merge(const RunningStatistics &other) noexcept {
    if (other.empty()) {
        return;
    }
    if (empty()) {
        *this = other;
        return;
    }

    const auto combined_count = count_ + other.count_;
    const double delta = other.mean_ - mean_;
    squared_deviation_sum_ += other.squared_deviation_sum_
                              + delta * delta * static_cast<double>(count_)
                                    * static_cast<double>(other.count_)
                                    / static_cast<double>(combined_count);
    mean_ += delta * static_cast<double>(other.count_) / static_cast<double>(combined_count);
    count_ = combined_count;
}

std::size_t qcd::statistics::RunningStatistics::count() const noexcept { return count_; }

bool qcd::statistics::RunningStatistics::empty() const noexcept { return count_ == 0; }

double qcd::statistics::RunningStatistics::mean() const {
    if (empty()) {
        throw std::logic_error("Mean requires at least one sample");
    }
    return mean_;
}

double qcd::statistics::RunningStatistics::population_variance() const {
    if (empty()) {
        throw std::logic_error("Population variance requires at least one sample");
    }
    return squared_deviation_sum_ / static_cast<double>(count_);
}

double qcd::statistics::RunningStatistics::sample_variance() const {
    if (count_ < 2) {
        throw std::logic_error("Sample variance requires at least two samples");
    }
    return squared_deviation_sum_ / static_cast<double>(count_ - 1);
}

double qcd::statistics::RunningStatistics::standard_error() const {
    return std::sqrt(sample_variance() / static_cast<double>(count_));
}

#include <cmath>
#include <gtest/gtest.h>
#include <qcd/observables.h>
#include <qcd/update.h>

template <class G> void structural_checks() {
    qcd::rng::RandomStream r(42);
    qcd::Field<G> f({4, 4, 4, 4});
    EXPECT_NEAR(qcd::action(f, 1.), 0., 1e-12);
    EXPECT_NEAR(qcd::wilson_loop(f, 2, 2), 1., 1e-12);
    f.hot(r);
    const std::vector<std::pair<std::size_t, std::size_t>> definitions{
        {1, 1}, {1, 3}, {2, 2}, {2, 3}};
    const auto cached = qcd::wilson_loops(f, definitions);
    for (std::size_t i = 0; i < definitions.size(); ++i)
        EXPECT_NEAR(cached[i], qcd::wilson_loop(f, definitions[i].first, definitions[i].second),
                    1e-13);
    const double old = qcd::action(f, 1.7);
    for (std::size_t mu = 0; mu < 4; ++mu) {
        const auto before = f.at(17, mu);
        const auto next = G::multiply(G::proposal(r, .8), before);
        const double delta = qcd::action_difference(f, 17, mu, next, 1.7);
        f.at(17, mu) = next;
        EXPECT_NEAR(qcd::action(f, 1.7) - old, delta, 1e-9);
        f.at(17, mu) = before;
    }
    const double loop = qcd::wilson_loop(f, 2, 3);
    const auto flux = qcd::field_samples(f, 2, 3, 0, 3);
    for (std::size_t dy = 0; dy < 4; ++dy)
        for (std::size_t dx = 0; dx < 4; ++dx) {
            const auto reflected_x = (2 + 8 - dx - 1) % 4, reflected_y = (8 - dy) % 4;
            EXPECT_NEAR(flux.ws[dy * 4 + dx], flux.ws[reflected_y * 4 + reflected_x], 1e-14);
        }
    std::vector<typename G::Link> transformations;
    for (std::size_t x = 0; x < f.geometry.volume(); ++x)
        transformations.push_back(G::hot(r));
    f.transform(transformations);
    EXPECT_NEAR(qcd::action(f, 1.7), old, 1e-9);
    EXPECT_NEAR(qcd::wilson_loop(f, 2, 3), loop, 1e-12);
    const auto transformed = qcd::field_samples(f, 2, 3, 0, 3);
    EXPECT_NEAR(flux.w, transformed.w, 1e-12);
    for (std::size_t i = 0; i < flux.s.size(); ++i) {
        EXPECT_NEAR(flux.s[i], transformed.s[i], 1e-12);
        EXPECT_NEAR(flux.ws[i], transformed.ws[i], 1e-12);
    }
}
TEST(Physics, U1GaugeInvarianceAndActionDifference) { structural_checks<qcd::U1>(); }
TEST(Physics, SU3GaugeInvarianceAndActionDifference) { structural_checks<qcd::SU3>(); }

TEST(Physics, GroupConstraintsAndInverseProposals) {
    qcd::rng::RandomStream r(123);
    auto product = qcd::SU3::identity();
    for (int i = 0; i < 2000; ++i) {
        const auto u = i % 2 ? qcd::SU3::proposal(r, .8) : qcd::SU3::hot(r);
        EXPECT_NEAR(std::abs(u.determinant() - std::complex<double>(1., 0.)), 0., 1e-12);
        EXPECT_TRUE((u.adjoint() * u).isApprox(qcd::SU3::identity(), 1e-12));
        product = qcd::SU3::multiply(product, u);
        EXPECT_NEAR(std::abs(qcd::U1::proposal(r, .8)), 1., 1e-14);
    }
    EXPECT_TRUE((product.adjoint() * product).isApprox(qcd::SU3::identity(), 1e-10));
}

TEST(Physics, ColdFluxVacuumSubtractionIsZero) {
    qcd::Field<qcd::SU3> f({4, 4, 4, 4});
    const auto samples = qcd::field_samples(f, 2, 2, 0, 3);
    for (std::size_t i = 0; i < samples.s.size(); ++i)
        EXPECT_DOUBLE_EQ(samples.ws[i] / samples.w - samples.s[i], 0.);
}

TEST(Physics, U1TwoDimensionalExactPlaquetteAndIndependentStarts) {
    // At beta=1 on a periodic 4x4 2D lattice, finite-volume corrections to I1/I0
    // are < 1e-4. This tests the sampler against a result independent of our action code.
    const double expected = std::cyl_bessel_i(1., 1.) / std::cyl_bessel_i(0., 1.);
    double means[2]{};
    for (std::size_t chain = 0; chain < 2; ++chain) {
        qcd::rng::RandomStream r(12, chain);
        qcd::Field<qcd::U1> f({4, 4});
        if (chain)
            f.hot(r);
        for (int step = 0; step < 5000; ++step) {
            qcd::metropolis(f, r, 1., 1.5);
            if (step >= 1000)
                means[chain] += (1. - qcd::action(f, 1.) / 16.) / 4000.;
        }
        EXPECT_NEAR(means[chain], expected, .025);
    }
    EXPECT_NEAR(means[0], means[1], .035);
}

TEST(Physics, SU3ZeroCouplingHotColdAndReproducibility) {
    double means[2]{};
    for (std::size_t chain = 0; chain < 2; ++chain) {
        qcd::rng::RandomStream r(91, chain);
        qcd::Field<qcd::SU3> f({4, 4, 4, 4});
        if (chain)
            f.hot(r);
        for (int step = 0; step < 120; ++step) {
            EXPECT_DOUBLE_EQ(qcd::metropolis(f, r, 0., 2.), 1.);
            if (step >= 40)
                means[chain] += (1. - qcd::action(f, 1.) / 1536.) / 80.;
        }
        EXPECT_NEAR(means[chain], 0., .01);
        for (const auto &u : f.links)
            EXPECT_TRUE((u.adjoint() * u).isApprox(qcd::SU3::identity(), 1e-11));
    }
    EXPECT_NEAR(means[0], means[1], .015);
    qcd::Field<qcd::U1> a({4, 4, 4, 4}), b({4, 4, 4, 4});
    qcd::rng::RandomStream r1(51), r2(51);
    for (int i = 0; i < 5; ++i) {
        qcd::metropolis(a, r1, 1., .6);
        qcd::metropolis(b, r2, 1., .6);
    }
    EXPECT_EQ(a.links, b.links);
}

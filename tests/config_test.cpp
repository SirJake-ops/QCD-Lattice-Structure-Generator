#include <array>
#include <cstdint>
#include <filesystem>
#include <string_view>

#include <gtest/gtest.h>
#include <toml++/toml.hpp>

#include <qcd/config.h>

namespace {

TEST(ConfigTest, ExampleFilesAreValidToml) {
    constexpr std::array config_files{
        "default.toml",
        "small-test.toml",
        "example-su3.toml",
    };

    for (const std::string_view filename : config_files) {
        const auto path = std::filesystem::path{QCD_CONFIG_DIR} / filename;
        toml::table config;

        ASSERT_NO_THROW(config = toml::parse_file(path.string()))
            << "Could not parse " << path;
        EXPECT_EQ(config["schema_version"].value<std::int64_t>(), 1)
            << "Unexpected schema version in " << path;
        EXPECT_TRUE(config.contains("model")) << "Missing [model] in " << path;
        EXPECT_TRUE(config.contains("lattice")) << "Missing [lattice] in " << path;
        EXPECT_TRUE(config.contains("sampling")) << "Missing [sampling] in " << path;
        EXPECT_TRUE(config.contains("output")) << "Missing [output] in " << path;
    }
}

TEST(ConfigTest, LoadsTypedDefaultConfiguration) {
    const auto path = std::filesystem::path{QCD_CONFIG_DIR} / "default.toml";
    const auto config = toml_config::load_config(path);

    EXPECT_EQ(config.schema_version, 1U);
    EXPECT_EQ(config.model_config.gauge_group, "u1");
    EXPECT_EQ(config.lattice_config.extents.size(), 4U);
    EXPECT_EQ(config.lattice_config.boundary_condition,
              toml_config::BoundaryCondition::periodic);
}

} // namespace

#include <exception>
#include <filesystem>
#include <iostream>

#include <qcd/config.h>

int main(int argc, char *argv[]) {
    const std::filesystem::path path_to_toml =
        argc > 1 ? std::filesystem::path{argv[1]} : std::filesystem::path{QCD_DEFAULT_CONFIG_PATH};

    try {
        const auto run_config = toml_config::load_config(path_to_toml);
        std::cout << "Parsed configuration: " << path_to_toml << "\n\n" << run_config;
    } catch (const std::exception &error) {
        std::cerr << "Unable to load configuration '" << path_to_toml << "': " << error.what()
                  << '\n';
        return 1;
    }

    return 0;
}

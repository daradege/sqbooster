"""
Configuration Manager Example - sqbooster

A configuration manager for applications with support for different
environments and settings.
"""

import sqbooster


class ConfigManager:
    def __init__(self):
        self.db = sqbooster.json("examples/app_config.json")
        self._load_defaults()

    def _load_defaults(self):
        defaults = {
            "app": {
                "name": "MyApp",
                "version": "1.0.0",
                "debug": False,
                "log_level": "INFO"
            },
            "database": {
                "host": "localhost",
                "port": 5432,
                "name": "myapp_db",
                "pool_size": 10
            },
            "api": {
                "base_url": "https://api.example.com",
                "timeout": 30,
                "retry_attempts": 3,
                "rate_limit": 100
            },
            "features": {
                "user_registration": True,
                "email_notifications": True,
                "analytics": False,
                "beta_features": False
            },
            "ui": {
                "theme": "light",
                "language": "en",
                "items_per_page": 20,
                "show_tooltips": True
            }
        }

        for section, settings in defaults.items():
            if not self.db.exists(section):
                self.db.write(section, settings)

    def get(self, section: str, key: str = None, default=None):
        section_data = self.db.read(section, {})
        if key is None:
            return section_data
        return section_data.get(key, default)

    def set(self, section: str, key: str, value):
        section_data = self.db.read(section, {})
        section_data[key] = value
        self.db.write(section, section_data)

    def update_section(self, section: str, updates: dict):
        section_data = self.db.read(section, {})
        section_data.update(updates)
        self.db.write(section, section_data)

    def get_environment_config(self, env: str = "development") -> dict:
        env_key = f"env:{env}"
        return self.db.read(env_key, {})

    def set_environment_config(self, env: str, config: dict):
        env_key = f"env:{env}"
        self.db.write(env_key, config)

    def export_config(self) -> dict:
        config = {}
        sections = ["app", "database", "api", "features", "ui"]
        for section in sections:
            if self.db.exists(section):
                config[section] = self.db.read(section)
        return config


def main():
    print("=== Configuration Manager Example ===\n")

    config = ConfigManager()

    print("Current App Configuration:")
    app_config = config.get("app")
    for key, value in app_config.items():
        print(f"  {key}: {value}")

    print("\nCurrent Database Configuration:")
    db_config = config.get("database")
    for key, value in db_config.items():
        print(f"  {key}: {value}")

    print("\n--- Updating Configuration ---")
    config.set("app", "debug", True)
    config.set("app", "log_level", "DEBUG")
    config.update_section("api", {
        "timeout": 60,
        "retry_attempts": 5
    })

    print("Updated app debug mode:", config.get("app", "debug"))
    print("Updated app log level:", config.get("app", "log_level"))
    print("Updated API timeout:", config.get("api", "timeout"))

    print("\n--- Environment Configurations ---")

    dev_config = {
        "database_url": "sqlite:///dev.db",
        "debug": True,
        "log_level": "DEBUG",
        "mock_external_apis": True
    }
    config.set_environment_config("development", dev_config)

    prod_config = {
        "database_url": "postgresql://user:pass@prod-db:5432/myapp",
        "debug": False,
        "log_level": "WARNING",
        "mock_external_apis": False
    }
    config.set_environment_config("production", prod_config)

    print("Development config:", config.get_environment_config("development"))
    print("Production config:", config.get_environment_config("production"))

    print("\n--- Feature Flags ---")
    features = config.get("features")
    print("Current features:")
    for feature, enabled in features.items():
        status = "+" if enabled else "-"
        print(f"  {status} {feature}")

    config.set("features", "beta_features", True)
    print(f"\nBeta features enabled: {config.get('features', 'beta_features')}")

    config.db.close()
    print("\nConfiguration management example completed!")


if __name__ == "__main__":
    main()

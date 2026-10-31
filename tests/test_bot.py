import unittest
from unittest.mock import Mock, patch

from telegram import Update

from app.bot import main


class TestBotStartup(unittest.TestCase):
    @patch("app.bot.CacheService")
    @patch("app.bot.cleanup_temp_dir")
    @patch("app.bot.Application.builder")
    @patch("app.bot.config.telegram_api_url", "")
    @patch("app.bot.config.bot_token", "test-token")
    def test_polling_retries_startup_network_errors(
        self, application_builder, cleanup_temp_dir, cache_service
    ):
        builder = Mock()
        builder.token.return_value = builder
        application = Mock()
        builder.build.return_value = application
        application_builder.return_value = builder

        main()

        application.run_polling.assert_called_once_with(
            allowed_updates=Update.ALL_TYPES,
            bootstrap_retries=-1,
        )


if __name__ == "__main__":
    unittest.main()

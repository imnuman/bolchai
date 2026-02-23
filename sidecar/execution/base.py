class BaseLanguage:
    name = "Language"
    aliases = []
    file_extension = ""

    def run(self, code):
        """Execute code, yield output chunks as dicts."""
        raise NotImplementedError

    def stop(self):
        """Stop current execution."""
        pass

    def terminate(self):
        """Clean up resources."""
        pass

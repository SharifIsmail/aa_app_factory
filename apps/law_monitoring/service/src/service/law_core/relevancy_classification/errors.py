class TeamNamesDoNotMatch(Exception):
    def __init__(self, team_names_a: set[str], team_names_b: set[str]) -> None:
        message = f"""team descriptions do not match
        team_names_a={team_names_a}
        team_names_b={team_names_b}
        """
        self.message = message
        super().__init__(self.message)

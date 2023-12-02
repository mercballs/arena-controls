from truefinals_api.api import (
    getAllGamesWithOneOrMoreCompetitors,
    getAllPlayersInTournament,
    getAllTourneys,
)
import json
from pathlib import Path
import logging
from pprint import pprint

class TrueFinals:
    def __init__(self, credential_file_location="./apicreds.json"):
        q = Path(credential_file_location)

        if not q.exists():
            q.touch()
            with open(q, "w") as fileitem:
                fileitem.write(json.dumps({"user_id": "", "api_key": ""}))
                logging.warn(
                    "User did not enter tokens yet, cannot access API.  Please change apicreds.json"
                )

        self._credentials = json.loads(open(q, "r").read())

    def getGamesWithNonZeroCompetitors(self, tournamentID: str) -> list[dict]:
        return getAllGamesWithOneOrMoreCompetitors(self._credentials, tournamentID)

    def getAllPlayersOfTournament(self, tournamentID: str) -> list[dict]:
        return getAllPlayersInTournament(self._credentials, tournamentID)

    def getAllTournaments(self) -> list[dict]:
        return getAllTourneys(self._credentials)
    
    #def getFInishedGames() ->
    # need to go for state: done in the match itself?

    def getUpcomingMatchesWithPlayers(self, tournamentID: str) -> list[dict]:
        matches_nonzero = self.getGamesWithNonZeroCompetitors(tournamentID)
        competitors = self.getAllPlayersOfTournament(tournamentID)

        def playerIDToName(competitors, playerID: str):
            for c in competitors:
                if c["id"] == playerID:
                    return c
            if playerID.startswith("bye"):
                return {"name":"Bye", "seed":-1,"wins":-1, "losses":-1, "ties":-1, "bye":True} #Special case for byes in the bracket.
            print(f"did not find competitor, oops!  Was looking for {playerID}")

        for match in matches_nonzero:
            for slot in match["slots"]:
                if slot["playerID"] != None:
                    player_backfill = playerIDToName(competitors, slot["playerID"])

                    if 'bye' in player_backfill: #exposing it for below filtering.
                        match['has_bye'] = True

                    slot["gscrl_friendly_name"] = player_backfill["name"]
                    slot["gscrl_seed"] = player_backfill["seed"]
                    slot["gscrl_wlt"] = {}
                    slot["gscrl_wlt"]["w"] = player_backfill["wins"]
                    slot["gscrl_wlt"]["l"] = player_backfill["losses"]
                    slot["gscrl_wlt"]["t"] = player_backfill["ties"]

        #Remove any match with a bye built in, so we only care about the real ones as-is.
        
        matches_nonzero = [x for x in matches_nonzero if not 'has_bye' in x]


        return matches_nonzero

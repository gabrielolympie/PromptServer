from pydantic import BaseModel, Field
from typing import Optional, List, Type, NewType, Union
from datetime import date, datetime
from uuid import UUID, uuid4
import math

from src.search.embedders import mistral_embeddings


class Movie(BaseModel):
    poster_link: Optional[str] = None
    series_title: Optional[str] = None
    released_year: Optional[int] = None
    certificate: Optional[str] = None
    runtime: Optional[str] = None
    genre: Optional[str] = None
    imdb_rating: Optional[float] = None
    overview: Optional[str] = None
    meta_score: Optional[int] = None
    director: Optional[str] = None
    star1: Optional[str] = None
    star2: Optional[str] = None
    star3: Optional[str] = None
    star4: Optional[str] = None
    no_of_votes: Optional[int] = None
    gross: Optional[str] = None

    id: UUID = Field(default_factory=uuid4)
    document: Optional[str] = None

    def __init__(self, **data):
        ## Pre init
        data = self.pre_init(data)

        # Initialize the parent class
        super().__init__(**data)

        # Post initialization
        self.post_init()

    def pre_init(self, data):
        # Get type annotations from the class
        type_hints = self.__annotations__

        # Remove NaN values and perform type checking with casting
        validated_data = {}
        for key, value in data.items():
            if isinstance(value, float) and math.isnan(value):
                continue

            if key in type_hints:
                # Handle Optional types and get the base type
                expected_type = type_hints[key]
                if hasattr(expected_type, "__origin__") and expected_type.__origin__ is Union:
                    # For Optional/Union types, get the first non-None type
                    args = expected_type.__args__
                    expected_type = next((arg for arg in args if arg is not type(None)), args[0])

                # Try to cast to the expected type if it doesn't match
                if value is None:
                    validated_data[key] = value
                else:
                    try:
                        if expected_type is int and isinstance(value, float):
                            # Special case for converting float to int
                            validated_data[key] = int(value)
                        elif not isinstance(value, expected_type):
                            # Try to cast to the expected type
                            validated_data[key] = expected_type(value)
                        else:
                            validated_data[key] = value
                    except (ValueError, TypeError):
                        # If casting fails, skip this value
                        continue
            else:
                validated_data[key] = value

        return validated_data

    def post_init(self):
        self.id = str(self.id)
        self.document = f"## Title\n{self.series_title or ''}\n\n## Overview\n{self.overview or ''}"

    def options(self):
        displayedAttributes = ["series_title", "released_year", "genre", "imdb_rating", "overview"]
        searchableAttributes = ["document"]
        filterableAttributes = ["released_year", "imdb_rating", "no_of_votes"]
        embedders = {
            # 'default': mistral_embeddings
        }

        return {
            "displayedAttributes": displayedAttributes,
            "searchableAttributes": searchableAttributes,
            "filterableAttributes": filterableAttributes,
            "embedders": embedders,
        }

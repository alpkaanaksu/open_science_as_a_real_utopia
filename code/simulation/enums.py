from enum import IntEnum

class SelectionStrategy(IntEnum):
    TRUTH = 0
    NOVELTY = 1

class PublicationBias(IntEnum):
    NONE = 0
    WEAK = 1
    STRONG = 2

class StudyType(IntEnum):
    ORIGINAL = 0
    REPLICATION = 1

class PublicationStatus(IntEnum):
    FILE_DRAWER = 0
    PUBLISHED = 1

class ResearcherActivityStatus(IntEnum):
    INACTIVE = 0
    ACTIVE = 1

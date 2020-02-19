from rasa.nlu.constants import TEXT, SPACY_DOCS, ENTITIES
from rasa.nlu.tokenizers.whitespace_tokenizer import WhitespaceTokenizer
from rasa.nlu.training_data import Message, TrainingData
from rasa.nlu.extractors.crf_entity_extractor import CRFEntityExtractor
from rasa.utils.tensorflow.constants import EPOCHS, RANDOM_SEED


def test_crf_extractor(spacy_nlp):
    examples = [
        Message(
            "anywhere in the west",
            {
                "intent": "restaurant_search",
                "entities": [
                    {"start": 16, "end": 20, "value": "west", "entity": "location"}
                ],
                SPACY_DOCS[TEXT]: spacy_nlp("anywhere in the west"),
            },
        ),
        Message(
            "central indian restaurant",
            {
                "intent": "restaurant_search",
                "entities": [
                    {
                        "start": 0,
                        "end": 7,
                        "value": "central",
                        "entity": "location",
                        "extractor": "random_extractor",
                    },
                    {
                        "start": 8,
                        "end": 14,
                        "value": "indian",
                        "entity": "cuisine",
                        "extractor": "CRFEntityExtractor",
                    },
                ],
                SPACY_DOCS[TEXT]: spacy_nlp("central indian restaurant"),
            },
        ),
    ]

    extractor = CRFEntityExtractor(
        component_config={
            "features": [
                ["low", "title", "upper", "pos", "pos2"],
                ["low", "suffix3", "suffix2", "upper", "title", "digit", "pos", "pos2"],
                ["low", "title", "upper", "pos", "pos2"],
            ],
            RANDOM_SEED: 1,
            EPOCHS: 75,
        }
    )
    tokenizer = WhitespaceTokenizer()

    training_data = TrainingData(training_examples=examples)
    tokenizer.train(training_data)
    extractor.train(training_data)

    sentence = "italian restaurant"
    message = Message(sentence, {SPACY_DOCS[TEXT]: spacy_nlp(sentence)})

    tokenizer.process(message)
    extractor.process(message)

    detected_entities = message.get(ENTITIES)

    assert len(detected_entities) == 1
    assert detected_entities[0]["entity"] == "cuisine"
    assert detected_entities[0]["value"] == "italian"

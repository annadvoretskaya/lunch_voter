from django.contrib.postgres.forms import SimpleArrayField
from django.forms import FloatField


class IntegerListField(SimpleArrayField):

    def __init__(self, delimiter=",", max_length=None, min_length=None, **kwargs):
        super().__init__(FloatField(), delimiter=delimiter, max_length=max_length, min_length=min_length, **kwargs)

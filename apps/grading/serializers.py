from rest_framework import serializers
from .models import GradingResult

class GradingResultSerializer(serializers.ModelSerializer):
    '''Serializer for GradingResult model.'''

    class Meta:
        model = GradingResult
        fields = ('id', 'submission', 'grading_method', 'performance_analysis',
                  'suggestions', 'summary', 'detailed_scores', 'created_at')
        read_only_fields = ('id', 'created_at')
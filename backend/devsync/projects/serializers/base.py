from rest_framework import serializers


class BaseChangeMemberRelationSerializer(serializers.ModelSerializer):
    relation_model = None
    relation_name = None
    member_relation_model = None
    not_found_error_message = 'Данной сущности нет в этом проекте.'
    already_exists_error_message = 'Эта сущность уже принадлежит данному пользователю.'
    not_exists_error_message = 'Эта сущность не принадлежит данному пользователю.'

    class Meta:
        fields = []

    def get_fields(self):
        fields = super().get_fields()
        fields[f"{self.relation_name}_id"] = serializers.IntegerField(write_only=True,required=True)
        return fields

    def _get_relation(self, relation_id):
        try:
            return self.relation_model.objects.get(
                id=relation_id,
                project=self.context['project']
            )
        except self.relation_model.DoesNotExist:
            raise serializers.ValidationError(
                {f"{self.relation_name}_id": self.not_found_error_message},
                code=f'{self.relation_name}_not_found'
            )

    def _check_relation_assignment(self, user, relation, exists=True):
        if self.member_relation_model.objects.filter(
            user=user,
            **{self.relation_name: relation}
        ).exists() != exists:
            error_message = self.already_exists_error_message if not exists else self.not_exists_error_message
            error_key = "already" if not exists else "not"
            raise serializers.ValidationError(
                {f"{self.relation_name}_id": error_message},
                code=f'{self.relation_name}_{error_key}_assigned'
            )

    def validate(self, data):
        relation_id = data.pop(f"{self.relation_name}_id")
        relation = self._get_relation(relation_id)
        data[self.relation_name] = relation

        member = self.context['member']
        request = self.context['request']

        if request.method == 'POST':
            self._check_relation_assignment(member.user, relation, exists=False)
        elif request.method == 'DELETE':
            self._check_relation_assignment(member.user, relation, exists=True)

        return data

    def create(self, validated_data):
        return self.member_relation_model.objects.create(
            user=self.context['member'].user,
            **{self.relation_name: validated_data[self.relation_name]}
        )
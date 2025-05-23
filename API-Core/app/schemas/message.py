from marshmallow import Schema, fields, validate

class MessageCreateSchema(Schema):
    item_id = fields.Int(required=True)
    content = fields.Str(required=True, validate=validate.Length(min=1, max=1000))

class MessageSchema(Schema):
    message_id = fields.Int()
    conversation_id = fields.Int()
    sender_id = fields.Int()
    receiver_id = fields.Int()
    content = fields.Str()
    sent_at = fields.DateTime()

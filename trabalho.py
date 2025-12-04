import json
import boto3
import uuid
from decimal import Decimal
from datetime import datetime
from boto3.dynamodb.conditions import Attr


DYNAMODB_TABLE = 'Tasks'
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(DYNAMODB_TABLE)


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def lambda_handler(event, context):
    print("Event:", json.dumps(event))
    
 
    route_key = event.get('routeKey')
    http_method = event['requestContext']['http']['method']
    path_parameters = event.get('pathParameters', {})
    query_string_parameters = event.get('queryStringParameters', {})
    
    body = None
    if event.get('body'):
        try:
            body = json.loads(event.get('body'))
        except:
            body = {}

    try:
       
        if route_key == 'POST /tasks':
            task_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()
            
            item = {
                'task_id': task_id,
                'titulo': body.get('titulo'),
                'descricao': body.get('descricao'),
                'data': body.get('data'), 
                'created_at': timestamp
            }
            
            table.put_item(Item=item)
            return build_response(201, {'message': 'Tarefa criada', 'id': task_id})

   
        elif route_key == 'GET /tasks':
            
            target_date = query_string_parameters.get('date') if query_string_parameters else None
            
            if target_date:
               
                response = table.scan(
                    FilterExpression=Attr('data').eq(target_date)
                )
            else:
               
                response = table.scan()
                
            items = response.get('Items', [])
            return build_response(200, items)

        
        elif route_key == 'GET /tasks/{id}':
            task_id = path_parameters.get('id')
            response = table.get_item(Key={'task_id': task_id})
            if 'Item' in response:
                return build_response(200, response['Item'])
            else:
                return build_response(404, {'message': 'Tarefa nao encontrada'})

  
        elif route_key == 'PUT /tasks/{id}':
            task_id = path_parameters.get('id')
            
           
            update_expression = "set "
            expression_values = {}
            expression_names = {}
            
            if 'titulo' in body:
                update_expression += "#t = :t, "
                expression_values[':t'] = body['titulo']
                expression_names['#t'] = 'titulo'
            
            if 'descricao' in body:
                update_expression += "descricao = :d, "
                expression_values[':d'] = body['descricao']
                
            if 'data' in body:
                update_expression += "#dt = :dt, "
                expression_values[':dt'] = body['data']
                expression_names['#dt'] = 'data'
            
  
            update_expression = update_expression.rstrip(', ')
            
            if not expression_values:
                 return build_response(400, {'message': 'Nenhum campo para atualizar'})

            table.update_item(
                Key={'task_id': task_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values,
                ExpressionAttributeNames=expression_names if expression_names else None
            )
            
            return build_response(200, {'message': 'Tarefa atualizada'})

        elif route_key == 'DELETE /tasks/{id}':
            task_id = path_parameters.get('id')
            table.delete_item(Key={'task_id': task_id})
            return build_response(200, {'message': 'Tarefa deletada'})

        else:
            return build_response(400, {'message': 'Rota nao suportada'})

    except Exception as e:
        print(e)
        return build_response(500, {'error': str(e)})

def build_response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps(body, cls=DecimalEncoder)
    }
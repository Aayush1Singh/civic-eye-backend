from services.similar_cases import get_similar_cases
from services.query_resolver import query_resolver
def get_answers_to_normal_query(session_id,query):
  return query_resolver(session_id,query)

def get_answer_to_similar_cases(query,session_id,user_id):
  return get_similar_cases(query,session_id,user_id)

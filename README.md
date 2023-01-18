# Production Plan API

This is a Flask API, exposed on the port 8888, that receives a JSON payload, processes it using the `production_plan` module and returns the result in json format.

## Endpoints

- `POST /productionplan`

## Usage

1. Clone the repository: 
```bash
git clone https://github.com/mathiasJty/production-plan-api.git
```
2. Install the requirements:
```bash
pip install -r requirements.txt
```
3. Run the API:
```bash
python app.py
```
4. Make a POST request to the API endpoint with a JSON 
payload or use the test module:
```bash
python test.py
```
In the test module you can replace the variable my_payload 
to the payload you want to test as a python object

5. Make sure that the payload is in the correct format and contains all the required fields.

## Error Handling
The API will return a 400 Bad Request error if the payload is not in a valid JSON format.

The API will return a 500 Internal Server Error if the production_plan module raises an exception.
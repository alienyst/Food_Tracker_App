from flask import Flask, render_template, g, request
from datetime import datetime
from database import connect_db, get_db

app = Flask(__name__)

@app.teardown_appcontext
def close_db(error):
	if hasattr(g, 'sqlite_db'):
		g.sqlite_db.close()

@app.route('/', methods=['POST', 'GET'])
def index():
	db = get_db()
	if request.method == 'POST':
		
		date =  request.form['date']
		dt = datetime.strptime(date, '%Y-%m-%d')
		dt_date = datetime.strftime(dt, '%Y%m%d')

		db.execute('insert into log_date(entry_date) values (?)', [dt_date])
		db.commit()

	cur = db.execute('''select log_date.entry_date, food.name, sum(food.carbohydrate) as carbohydrate, 
						sum(food.fat) as fat, sum(food.calories) as calories, sum(food.protein) as protein 
						from log_date left join food_date on food_date.log_date_id = log_date.id 
						left join food on food.id=food_date.food_id 
						group by log_date.id 
						order by log_date.entry_date desc''')
	results = cur.fetchall()

	date_result = []

	for i in results:
		single_date = {}
		single_date['date'] = i['entry_date']
		single_date['protein'] = i['protein']
		single_date['carbohydrate'] = i['carbohydrate']
		single_date['fat'] = i['fat']
		single_date['calories'] = i['calories']

		d = datetime.strptime(str(i['entry_date']), '%Y%m%d')
		single_date['entry_date'] = datetime.strftime(d, '%B %d, %Y')
		date_result.append(single_date)

	return render_template('home.html', results=date_result)

@app.route('/view/<date>', methods=['GET', 'POST'])
def view(date):

	db = get_db()

	cur = db.execute('select id, entry_date from log_date where entry_date = ?', [date])
	date_result = cur.fetchone()

	if request.method == 'POST':
		db.execute('insert into food_date(food_id, log_date_id) values(?,?)', [request.form['food_select'], date_result['id']])
		db.commit()

	d = datetime.strptime(str(date_result['entry_date']), '%Y%m%d')
	pretty_date = datetime.strftime(d, '%B %d, %Y')

	food_cur = db.execute('select id, name from food')
	food_results = food_cur.fetchall()

	log_cur = db.execute('''select food.name, food.carbohydrate, food.fat, food.calories, 
							food.protein from log_date join food_date on food_date.log_date_id = log_date.id 
							join food on food.id=food_date.food_id where log_date.entry_date = ?''', [date])
	log_results = log_cur.fetchall()

	totals = {}
	totals['protein'] = 0
	totals['carbohydrate'] = 0
	totals['fat'] = 0
	totals['calories'] = 0

	for food in log_results:
		totals['protein'] += food['protein']
		totals['carbohydrate'] += food['carbohydrate']
		totals['fat'] += food['fat']
		totals['calories'] += food['calories']

	return render_template('day.html', date=pretty_date, entry_date=date_result['entry_date'], food_results=food_results, log_results=log_results, totals=totals)

@app.route('/food', methods=['GET','POST'])
def food():
	db = get_db()

	if request.method == 'POST':
		name = request.form['food_name']
		protein = int(request.form['protein'])
		carbohydrates = int(request.form['carbohydrates'])
		fat = int(request.form['fat'])

		calories = protein * 4 + carbohydrates * 4 + fat * 9

		
		db.execute('insert into food(name, protein, carbohydrate, fat, calories) values (?,?,?,?,?)',
			[name, protein, carbohydrates, fat, calories])
		db.commit()

	cur = db.execute('select name, protein, carbohydrate, fat, calories from food')
	results = cur.fetchall()

	return render_template('add_food.html', results=results)

if __name__ == '__main__':
	app.run(debug=True)
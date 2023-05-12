from flask import Flask, render_template, redirect, url_for, request
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField
from werkzeug.utils import secure_filename
import os
import re
import plotly.express as px
import pandas as pd
import json
import string
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import plotly.graph_objs as go
from plotly.offline import plot
import matplotlib.pyplot as plt
from matplotlib import colors
from wordcloud import WordCloud, STOPWORDS


working_directory = os.getcwd()
path = working_directory
app = Flask(__name__)
f_name = ''
who_said_what = {}
app.config['SECRET_KEY'] = 'SecretIsNoSecret'
app.config['UPLOAD_FOLDER'] =  'uploads/'
class UploadFileForm(FlaskForm):
	file = FileField("File")
	submit = SubmitField('Upload File')

@app.route('/upload',methods=['GET','POST'])
def upload():
	form = UploadFileForm()
	if form.validate_on_submit():
		file = form.file.data
		f_name = file.filename
		with open(working_directory + '/data/file_name.txt', 'w') as f:
			f.write(f_name)
		file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),app.config['UPLOAD_FOLDER'],secure_filename(file.filename)))
		return redirect(url_for('main'))
	return render_template('index.html', form = form)
@app.route('/',methods=['GET','POST'])
@app.route('/home')
def home():
	return render_template('test_Homepage.html')
@app.route('/chart')
def chart():
	return render_template('chart_test.html')
@app.route('/running')
def main():
	f_name = ""
	working_directory = os.getcwd()
	with open(working_directory + '/data' + '/file_name.txt', 'r') as f_n:
		for line in f_n.readlines():
			f_name = line
			break
	with open(working_directory + '/data' + '/file_name.txt', 'r+') as f_n:
		f_n.truncate(0)
	path = working_directory + '/uploads/' + f_name

	with  open(path,encoding =  'utf8') as file:
		loader = json.load(file)
		keysList = list(loader.keys())

	comments = loader['comments'][1]
	commentslist = comments.keys()

#part 3 code
	display_name_list = {}
	messages = {}
	count = 0

#assigns a number to each specific name
	for i in range(len(loader['comments'])):
		line = loader['comments'][i]['commenter']['display_name']
		if line not in display_name_list:
			display_name_list[line] = count
			count += 1
	for i in range(len(loader['comments'])):
		name = loader['comments'][i]['commenter']['display_name']
		message = loader['comments'][i]['message']['body']
		#minor data preprocessing
		message = re.sub(r'http\S+','' ,message)
		message = re.sub('.com','',message)
		message = message.lower() 
		if len(message.split()) >= 7:
			if 'subscribed' not in message:
				messages[message] = display_name_list[name]

#creates a dict of who said what, what being a list

	for name in display_name_list:
		they_said = []
		for m in messages:
			if display_name_list[name] == messages[m]:
				they_said.append(m)
		if len(they_said) != 0: # Makes sure that they_said is not empty
			who_said_what[name] = they_said


	print('who_said_what loop finished')
	with open(working_directory + '/data/who_said_what.json', 'w') as wsw:
		wsw.write(json.dumps(who_said_what))
	return redirect(url_for('options_form'))
@app.route('/options', methods=['GET','POST'])
def options_form():
	
	if request.method == 'POST':
		if request.form.get('Sentiment') == 'Sentiment':
			print('Sentiment')
			return redirect(url_for('sentiment_finder'))
		elif request.form.get('Word Count') == 'Word Count':
			print('Word Count')
			return redirect(url_for('phrase_searcher'))
		else:
			print('both')
			return render_template('options.html')
	elif request.method == 'GET':
		print('No Post')
	return render_template('options.html')

@app.route('/sentiment', methods=['GET','POST'])
def sentiment_finder():
	srch_name = request.form.get("search_name")
	dp_name = srch_name
	working_directory = os.getcwd()
	obj = SentimentIntensityAnalyzer()
	sentiment_holder = {}
	sentiment_holder_avg = {}
	who_said_what = {}
	'''
	loads who_said_what to the function based on the upload from main()
	
	'''
	cp = 0
	ng = 0
	ps = 0
	ne = 0
	with open(working_directory + '/data/who_said_what.json',encoding =  'utf8') as f:
		who_said_what = json.load(f)
	
	
	with open(working_directory + '/data/search_name.txt', 'w') as f:
			f.write(str(dp_name))
			
			
	who = who_said_what.keys() # holds everyone that we included in who_said_what
	if request.method == 'POST':
		if(dp_name == 'all'):
			total_chat_values = {'compound': 0, 'neg': 0, 'pos': 0, 'neu': 0}
			account_cnt = 0
			for account in who_said_what:
				for what in who_said_what[account]:
					sentiment_holder[what] = obj.polarity_scores(what)
				for phrase in sentiment_holder:
					total_com = 0
					total_neg = 0
					total_pos = 0
					total_neu = 0

					total_com += sentiment_holder[phrase]['compound']
					total_neg += sentiment_holder[phrase]['neg']
					total_pos += sentiment_holder[phrase]['pos']
					total_neu += sentiment_holder[phrase]['pos']

				account_cnt += 1
				total_chat_values['compound'] += total_com
				total_chat_values['neg'] += total_neg
				total_chat_values['pos'] += total_pos
				total_chat_values['neu'] += total_neu

			total_com_all = total_chat_values['compound']/account_cnt
			total_neg_all = total_chat_values['neg']/account_cnt
			total_pos_all = total_chat_values['pos']/account_cnt
			total_neu_all = total_chat_values['neu']/account_cnt
			
			cp = round(total_com_all,2)
			ng = round(total_neg_all,2)
			ps = round(total_pos_all,2)
			ne = round(total_neu_all,2)
			
			sentiment_holder_avg = {'total_com_all': total_com_all,
					'total_neg_all' :total_neg_all,
					'total_pos_all':total_pos_all,
					'total_neu_all':total_neu_all}
		
		else:
			for what in who_said_what[dp_name]:
				sentiment_holder[what]= obj.polarity_scores(what)
			total_com = 0
			total_neg = 0
			total_pos = 0
			total_neu = 0

			for phrase in sentiment_holder:
				total_com += sentiment_holder[phrase]['compound']
				total_neg += sentiment_holder[phrase]['neg']
				total_pos += sentiment_holder[phrase]['pos']
				total_neu += sentiment_holder[phrase]['neu']
			total_com = total_com/len(sentiment_holder)
			total_neg = total_neg/len(sentiment_holder)
			total_pos = total_pos/len(sentiment_holder)
			total_neu = total_neu/len(sentiment_holder)
			
			cp = round(total_com,2)
			ng = round(total_neg,2)
			ps = round(total_pos,2)
			ne = round(total_neu,2)
			
			sentiment_holder_avg = {'total_com_all': total_com,
					'total_neg_all' :total_neg,
					'total_pos_all':total_pos,
					'total_neu_all':total_neu}
		#pie_chart_maker(total_pos,total_neg,total_neu)
		#max_min(sentiment_holder)
		with open(working_directory + '/data/sentiment_holder.json', 'w') as sh:
			sh.write(json.dumps(sentiment_holder))
		with open(working_directory + '/data/sentiment_holder_avg.json', 'w') as sha:
			sha.write(json.dumps(sentiment_holder_avg))
		return render_template('output.html', name = dp_name, compound = cp,negative = ng,positive = ps,neutral = ne)
	if request.method == 'GET':
		return render_template('sentiment-preview.html', display_name = who)

@app.route('/pie')
def pie_chart_maker():
	sentiment_holder_avg = {}
	search_name = ""
	with open(working_directory + '/data/sentiment_holder_avg.json',encoding = 'utf8') as f:
		sentiment_holder_avg = json.load(f)
	with open(working_directory + '/data' + '/search_name.txt', 'r') as f_n:
		for line in f_n.readlines():
			search_name = line
			break
	with open(working_directory + '/data' + '/search_name.txt', 'r+') as f_n:
		f_n.truncate(0)
	#for key in sentiment 
	posi = sentiment_holder_avg['total_pos_all']
	nega = sentiment_holder_avg['total_neg_all']
	neut = sentiment_holder_avg['total_neu_all']
	comp = sentiment_holder_avg['total_com_all']
	values = [posi,nega,neut]
	
	
	names = ['Positive', 'Negative', 'Neutral']
	data = [posi,nega,neut]
	color = ['red','blue','grey']
	removal_list = []
	
	
	
	data = [['Positive',posi], ['Negative',nega], ['Neutral',neut]]
	df = pd.DataFrame(data, columns= ['Value','Score']) 
	
	
	str_title =  'Sentiment Percentage: ' + search_name
	chrt = px.pie(df, values= 'Score', names = 'Value',color = 'Value',
		color_discrete_map= {'Positive':'red','Negative':'blue','Neutral':'grey'},
		hover_name = 'Score',labels={'Value':'Sentiment Type'},
		title = str_title ,template = 'plotly_dark',
		width = 800, height = 500, hole = 0)
	#graphJson = json.dumps(chrt, cls=plotly.utils.PlotlyJSONEncoder)
	#Figure.pie(chrt,labels = names,colors = color, autopct =  '%1.1f%%')
	chrt.show()
	return render_template('output.html',name = search_name,
					compound = round(comp,2),
					negative = round(nega,2),
					positive = round(posi,2),
					neutral = round(neut,2))
@app.route('/wordcloud')

def wordcloud():
	obj = SentimentIntensityAnalyzer()
		
	who_said_what = {}
	positive_cmt = []
	negative_cmt = []
	postive_cmt_words_cnt = {}
	negative_cmt_words_cnt = {}
	
	working_directory = os.getcwd()
	with open(working_directory + '/data/who_said_what.json',encoding =  'utf8') as f:
		who_said_what = json.load(f)
	
	for who in who_said_what:
		for comment in who_said_what[who]:
			value = obj.polarity_scores(comment)
			pos_val = value['pos']
			neg_val = value['neg']
			neu_val = value['neu']
			
			if pos_val > neu_val and pos_val > neg_val:
 				positive_cmt.append(comment)
			if neg_val > neu_val and neg_val > pos_val:
				negative_cmt.append(comment)
	
	for cmt in positive_cmt:
		words = cmt.split()
		for word in words:
			score = obj.polarity_scores(word)
			if score['neu']  != 1:
				if word not in postive_cmt_words_cnt.keys():
					postive_cmt_words_cnt[word] = 1
				else:
					postive_cmt_words_cnt[word] += 1
	for cmt in negative_cmt:
		words = cmt.split()
		for word in words:
			score = obj.polarity_scores(word)
			if score['neu']  != 1:
				if word not in negative_cmt_words_cnt.keys():
					negative_cmt_words_cnt[word] = 1
				else:
					negative_cmt_words_cnt[word] += 1
	
			
	
	num = 25
	neg_res = dict(sorted(negative_cmt_words_cnt.items(), key = lambda x:x[1], reverse=True)[:num])
	pos_res = dict(sorted(postive_cmt_words_cnt.items(), key = lambda x:x[1], reverse=True)[:num])
	
	
	df1 = pd.DataFrame(list(neg_res.items()), columns = ['Word', 'Count'])
	df1['Value'] = 'neg'
	df2 = pd.DataFrame(list(pos_res.items()), columns = ['Word', 'Count'])
	df2['Value'] = 'pos'
	wc = ''.join
	
	p_text = ' '.join(positive_cmt)
	n_text= ' '.join(negative_cmt)
	main_text = p_text + ' ' + n_text
	
	df_comb = pd.concat([df1, df2], ignore_index=True)
	df_comb = df_comb.drop_duplicates(subset='Word')
	
	def word_color(*args, **kwargs):
		word = args[0]
		value = df_comb.loc[df_comb['Word'] == word]['Value'].to_string()
		
		value_list = value.split(' ')
		if len(value_list) == 5:
			
			if value_list[4] == 'neg':
				return colors.to_hex('red')
			else:
				return colors.to_hex('blue')

	text = main_text
	for word in df_comb['Word']:
		text = text + word + ' '
	wordcloud = WordCloud(width = 800, height = 800,
	background_color = '#2D3033', colormap= 'coolwarm').generate(text)
	
	
	# plot the WordCloud image                            
	plt.figure(figsize = (8, 8), facecolor = None)
	plt.imshow(wordcloud)
	plt.axis("off")
	plt.tight_layout(pad = 0)

	plt.savefig("static/images/wordcloud.png")
	path = os.path.abspath("images/wordcloud.png")
	
	wordcloud = WordCloud(width = 800, height = 800,
	background_color = '#2D3033', colormap= 'autumn').generate(p_text)
	
	
	# plot the WordCloud image                            
	plt.figure(figsize = (8, 8), facecolor = None)
	plt.imshow(wordcloud)
	plt.axis("off")
	plt.tight_layout(pad = 0)

	plt.savefig("static/images/wordcloudpos.png")
	
	wordcloud = WordCloud(width = 800, height = 800,
	background_color = '#2D3033', colormap= 'winter').generate(n_text)
	
	
	# plot the WordCloud image                            
	plt.figure(figsize = (8, 8), facecolor = None)
	plt.imshow(wordcloud)
	plt.axis("off")
	plt.tight_layout(pad = 0)

	plt.savefig("static/images/wordcloudneg.png")
	
	return render_template('wordcloud.html')

				
@app.route('/wordcount', methods=['GET','POST'])
def phrase_searcher():

	who_said_what = dict()
	phrase = request.form.get("phrase")
	phrase = str(phrase)
	
	with open(working_directory + '/data/who_said_what.json',encoding =  'utf8') as f:
		who_said_what = json.load(f)
	phr = phrase.lower()
	apr_count = 0
	if request.method == 'POST':
		for person in who_said_what:
			for sentence in who_said_what[person]:
				if phr in sentence:
					apr_count += 1
		return render_template('wordcount.html',word_phrase = phrase,
						count = apr_count)
						 
	elif request.method == 'GET':
		return render_template('wordcount.html')
		
if  __name__ == '__main__':
	app.run(debug=True)

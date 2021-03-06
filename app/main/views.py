#coding:utf8

from .. import db
from . import main
from ..models import User, Role, Permission, Post, Comment, PostTag
from flask_login import login_required, current_user
from datetime import datetime
from ..decorators import admin_required, permission_required
from .forms import NameForm, EditProfileForm, EditProfileAdminForm, PostForm, CommentForm, NewEditProfileForm
from flask import render_template, session, redirect, url_for, current_app, abort, flash, request, make_response


@main.route("/", methods = ['GET', 'POST'])
def index():
	page = request.args.get('page', 1, type = int)
	show_followed = False
	if current_user.is_authenticated:
		show_followed = bool(request.cookies.get('show_followed', ''))
	if show_followed:
		query = current_user.followed_posts
	else:
		query = Post.query
	pagination = query.order_by(Post.timestamp.desc()).paginate(
		page, per_page = current_app.config['FLASK_POSTS_PER_PAGE'], error_out = False)
	posts = pagination.items
	return render_template('index.html', posts = posts, show_followed = show_followed, pagination = pagination)

@main.route('/add_new_post', methods = ['GET', 'POST'])
@login_required
def add_new_post():
	form = PostForm()
	if current_user.can(Permission.WRITE_ARTICLE) and form.validate_on_submit():
		final_edit_time = datetime.utcnow()
		if form.edittime.data != "":
			splittime = form.edittime.data.split("-")
			if len(splittime) == 3:
				final_edit_time = datetime(int(splittime[0]), int(splittime[1]), int(splittime[2]))

		for tag in form.tags.data:
			postTag = PostTag.query.filter_by(body=tag.body).first()
			if postTag is None:
				db.session.add(tag)

		post = Post(body = form.body.data, title = form.title.data, post_tags = form.tags.data, brief = form.brief.data, author = current_user._get_current_object(), timestamp = final_edit_time)
		db.session.add(post)
		return redirect(url_for('.index'))
	return render_template('add_new_post.html', form = form)

@main.route('/all')
@login_required
def show_all():
	resp = make_response(redirect(url_for('.index')))
	resp.set_cookie('show_followed', '', max_age = 30 * 24 * 60 * 60)
	return resp

@main.route('/followed')
@login_required
def show_followed():
	resp = make_response(redirect(url_for('.index')))
	resp.set_cookie('show_followed', '1', max_age = 30 * 24 * 60 * 60)
	return resp

@main.route('/user/<username>', methods = ['GET', 'POST'])
def user(username):
	# page = request.args.get('page', 1, type = int)
	user = User.query.filter_by(username = username).first()
	if user is None:
		abort(404)
	# pagination = user.posts.order_by(Post.timestamp.desc()).paginate(page, 
	# 	per_page = current_app.config['FLASK_POSTS_PER_PAGE'], error_out = False)
	# posts = pagination.items
	return render_template('new_user.html', user = user)

@main.route('/edit-profile', methods = ['GET', 'POST'])
@login_required
def edit_profile():
	form = NewEditProfileForm()
	if form.validate_on_submit():
		current_user.all_info = form.all_info.data
		db.session.add(current_user)
		flash('Your profile has been updated.')
		return redirect(url_for('.user', username = current_user.username))
	form.all_info.data = current_user.all_info
	return render_template('new_edit_profile.html', form = form)

@main.route('/edit-profile/<int:id>', methods = ['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
	user = User.query.get_or_404(id)
	form = EditProfileAdminForm(user = user)
	if form.validate_on_submit():
		user.username = form.username.data
		user.email = form.email.data
		user.confirmed = form.confirmed.data
		user.role = Role.query.get(form.role.data)
		user.name = form.name.data
		user.location = form.location.data
		user.about_me = form.about_me.data
		db.session.add(user)
		flash('Your profile has been updated.')
		return redirect(url_for('.user', username = user.username))
	form.email.data = user.email
	form.username.data = user.username
	form.confirmed.data = user.confirmed
	form.role.data = user.role_id
	form.name.data = user.name
	form.location.data = user.location
	form.about_me.data = user.about_me
	return render_template('edit_profile.html', form = form, user = user)

@main.route('/post/<int:id>', methods = ['GET', 'POST'])
def post(id):
	post = Post.query.get_or_404(id)
	form = CommentForm()
	if form.validate_on_submit():
		comment = Comment(body = form.body.data,
							post = post,
							author = current_user._get_current_object())
		db.session.add(comment)
		flash('Your comment has been publish.')
		return redirect(url_for('.post', id = post.id, page = -1))
	page = request.args.get('page', 1, type = int)
	if page == -1:
		page = (post.comments.count() - 1) / \
			current_app.config['FLASKY_COMMENTS_PER_PAGE'] + 1
	pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
		page, per_page = current_app.config['FLASKY_COMMENTS_PER_PAGE'], error_out = False)
	comments = pagination.items
	return render_template('post.html', post=post, form = form, comments = comments, pagination = pagination)

@main.route('/edit/<int:id>', methods = ['GET', 'POST'])
def edit_post(id):
	post = Post.query.get_or_404(id)
	if current_user != post.author and \
		not current_user.can(Permission.ADMINISTRATOR):
		abort(403)
	form = PostForm()
	if form.validate_on_submit():
		post.body = form.body.data
		post.title = form.title.data
		post.brief = form.brief.data
		post.post_tags = form.tags.data
		final_edit_time = form.edittime.data
		if form.edittime.data != "":
			splittime = form.edittime.data.split("-")
			print(str(len(splittime)))
			if len(splittime) == 3:
				final_edit_time = datetime(int(splittime[0]), int(splittime[1]), int(splittime[2]))
		post.timestamp = final_edit_time
		db.session.add(post)
		flash('The post has been updated.')
		return redirect(url_for('.post', id = post.id))
	form.body.data = post.body
	form.title.data = post.title
	form.brief.data = post.brief
	form.edittime.data = post.timestamp
	form.tags.data = post.post_tags
	return render_template('edit_post.html', form = form)

@main.route('/del_post/<int:id>', methods = ['GET', 'POST'])
@login_required
@permission_required(Permission.WRITE_ARTICLE)
def del_post(id):
	if id is not None:
		post = Post.query.filter_by(id=id).first()
		db.session.delete(post)
		db.session.commit()
		return redirect(url_for('.index'))

@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
	user = User.query.filter_by(username = username).first()
	if user is None:
		flash('无效的用户')
		return redirect(url_for('.index'))
	if current_user.is_following(user):
		flash('你已经关注过这位用户')
		return redirect(url_for('.user', username = username))
	current_user.follow(user)
	flash('你关注用户%s成功.' % username)
	return redirect(url_for('.user', username = username))

@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
	user = User.query.filter_by(username = username).first()
	if user is None:
		flash('无效的用户')
		return redirect(url_for('.index'))
	if not current_user.is_following(user):
		flash('你没有关注过这位用户')
		return redirect(url_for('.user', username = username))
	current_user.unfollow(user)
	flash('你取消关注用户%s成功！' % username)
	return redirect(url_for('.user', username = username))

@main.route('/followers/<username>')
def followers(username):
	user = User.query.filter_by(username = username).first()
	if user is None:
		flash('无效的用户')
		return redirect(url_for('.index'))
	page = request.args.get('page', 1, type = int)
	pagination = user.followers.paginate(page, per_page = current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
		error_out = False)
	follows = [{'user': item.follower, 'timestamp': item.timestamp}
				for item in pagination.items]
	return render_template('followers.html', user = user, title = 'Followers of',
		endpoint = '.followers', pagination = pagination, follows = follows)

@main.route('/followed_by/<username>')
def followed_by(username):
	user = User.query.filter_by(username = username).first()
	if user is None:
		flash('无效的用户')
		return redirect(url_for('.index'))
	page = request.args.get('page', 1, type = int)
	pagination = user.followed.paginate(page, per_page = current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
		error_out = False)
	follows = [{'user': item.followed, 'timestamp': item.timestamp}
				for item in pagination.items]
	return render_template('followers.html', user = user, title = 'Followed by',
		endpoint = '.followed_by', pagination = pagination, follows = follows)

@main.route('/moderate')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate():
	page = request.args.get('page', 1, type = int)
	pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
		page, per_page = current_app.config['FLASKY_COMMENTS_PER_PAGE'], error_out = False)

	comments = pagination.items
	return render_template('moderate.html', comments = comments, pagination = pagination, page = page)

@main.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_enable(id):
	comment = Comment.query.get_or_404(id)
	comment.disabled = False
	db.session.add(comment)
	return redirect(url_for('.moderate', page = request.args.get('page', 1, type = int)))

@main.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_disable(id):
	comment = Comment.query.get_or_404(id)
	comment.disabled = True
	db.session.add(comment)
	return redirect(url_for('.moderate', page = request.args.get('page', 1, type = int)))
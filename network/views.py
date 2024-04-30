from django.core.serializers import serialize
from django.core.paginator import Paginator
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
import json

from rest_framework.renderers import JSONRenderer

from .models import User, Post, Relationship
from .serializers import PostSerializer

def index(request):
    return render(request, "network/index.html")


def login_view(request):
    if request.method == "POST":

        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")

def modify_post(request, id):
    post = Post.objects.get(id=id)
    
    if request.user != post.author:
        return HttpResponse('You do not have permission to edit this post', status=403)

    data = json.loads(request.body)
    post.message = data['message']
    post.save()
    
    return JsonResponse({'message' : data['message']}, status=200)    

def follow(request, username):
    user = User.objects.get(username=username)

    if request.user == user:
        return HttpResponse('You cannot follow yourself', status=403)

    follow_object = user.relationships_to.filter(from_user=request.user, status=1)

    if follow_object:
        follow_object.delete()
        is_followed = False
    else:
        follow_object = Relationship(from_user=request.user, to_user=user, status=1)
        follow_object.save()
        is_followed = True

    response = {
        'username' : user.username,
        'post_count' : user.posts.count(),
        'following' : user.relationships_from.count(),
        'followed_by' : user.relationships_to.count(),
        'is_followed' : is_followed,
        'join_date' : f'{user.date_joined.strftime("%B")} {user.date_joined.strftime("%Y")}',
        'requested_by' : request.user.username if request.user.is_authenticated else None,
    }
    return JsonResponse(response, status=200)    

def get_user_profile(request, username):
    user = User.objects.get(username=username)
    
    if not request.user.is_authenticated:
        is_followed = False
    elif user.relationships_to.filter(from_user=request.user, status=1):
        is_followed = True
    else:
        is_followed = False

    response = {
        'username' : user.username,
        'post_count' : user.posts.count(),
        'following' : user.relationships_from.count(),
        'followed_by' : user.relationships_to.count(),
        'is_followed' : is_followed or None,
        'join_date' : f'{user.date_joined.strftime("%B")} {user.date_joined.strftime("%Y")}',
        'requested_by' : request.user.username if request.user.is_authenticated else None,
    }
    return JsonResponse(response, status=200)

def get_posts(request):
    pageNumber = int(request.GET.get("page"))
    postsPerPage = int(request.GET.get("perPage"))
    user = request.GET.get("user") or None
    feed = request.GET.get("feed") or None
    if feed:
        follow_relationships = request.user.relationships_from.filter(status=1) # Relationships 
        following = User.objects.filter(id__in=follow_relationships.values('to_user')) # Users
        posts = Post.objects.filter(author__in=following) # Posts       
    elif user:
        user_obj = User.objects.get(username=user)
        posts = Post.objects.filter(author=user_obj)  
    else:
        posts = Post.objects.all()

    paginator = Paginator(posts, postsPerPage)
    page = paginator.get_page(pageNumber)
    serializer = PostSerializer(page, many=True)

    response = {
        "requested_by" : request.user.username,
        "page" : pageNumber,
        "page_count" : paginator.num_pages,
        "has_next_page" : page.has_next(),
        "has_previous_page" : page.has_previous(),
        "posts" : serializer.data,
    }
    return JsonResponse(response, status=200)

def like_post(request, id):
    post = Post.objects.get(id=id)
    state = json.loads(request.body)['state']
    if state == 'like':
        post.liked_by.add(request.user)
    elif state == 'unlike':
        post.liked_by.remove(request.user)
    post.save()
    response = {
        'state': "unlike" if state == "like" else "like",
        'likes' : post.liked_by.count(),
    }
    return JsonResponse(response, status=200)

def submit_post(request):
    if request.method != "POST":
        return render(request, "index.html")  

    data = json.loads(request.body)
    post = Post(author=request.user, message=data['message'])
    post.save()
    serializer = PostSerializer(post)
    return JsonResponse(serializer.data, status=200)
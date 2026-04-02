from django.shortcuts import render,redirect
from .models import Book
from django.http import HttpResponse
from readingapp.models import *
from django.contrib import messages

from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
 
from django.contrib.auth import authenticate, login as auth_login, logout
# Create your views here.

  

def homepage(request):
    queryset = Book.objects.all().order_by('-id')

    if request.GET.get('search'):
        queryset = queryset.filter(
            book_name__icontains=request.GET.get("search")
        )

    queryset = queryset[:6].values()   # ✅ slice AFTER filter

    context = {'viewbook': queryset}
    return render(request, 'readingapp/homepage.html', context)

   
def show(request):
    request.method=="POST" in request.POST
    user=Book.objects.all().values()
    return render(request,"readingapp/bookdata.html",{'users':user})  


def register(request):
    if request.method=="POST" and 'submit' in request.POST:
        # nm= request.POST.get('unm')
        # print(nm)
        user = Book ( 
        username=request.POST.get('unm'),
        email=request.POST.get('ue'),
        book_name=request.POST.get('bn'),
        author_name=request.POST.get('an'),
        book_category=request.POST.get('bcat'),
        book_chapter=request.POST.get('cn'),
        book_pages=request.POST.get('pn'),
        book_agegroup=request.POST.get('ag'),
        book_img = request.FILES.get('bfile'),
        book_file = request.FILES.get('bpdf')),
        
        user.save()
        print(user)
        
    return render(request,"home.html")
@login_required(login_url="/login")

def addbook(request):

    category = request.GET.get('category')

    if category and category != "All":
        viewbook = Book.objects.filter(book_category=category)
    else:
        viewbook = Book.objects.all()

    if request.method == "POST":

        email = request.POST.get('email')
        username = request.POST.get('username')
        book_name = request.POST.get('book_name')
        author_name = request.POST.get('author_name')
        book_chapter = request.POST.get('book_chapter')
        book_category = request.POST.get('book_category')
        book_pages = request.POST.get('book_pages')
        book_agegroup=request.POST.get('book_agegroup')

        book_file = request.FILES.get('book_file')
        book_img = request.FILES.get('book_img')

        Book.objects.create(
            email=email,
            username=username,
            book_name=book_name,
            author_name=author_name,
            book_chapter=book_chapter,
            book_category=book_category,
            book_pages=book_pages,
            book_agegroup=book_agegroup,
            book_file=book_file,
            book_img=book_img
        )

        return redirect('/addbook/')

    context = {'viewbook':viewbook}
    return render(request,'readingapp/addbook.html',context)


def category_books(request, category):

    books = Book.objects.filter(book_category=category)

    context = {
        'books': books,
        'category': category
    }

    return render(request,'readingapp/category_books.html',context)
def category_books(request, category):
    
    # Check if category is age group (Kids/Young/Adult)
    if category in ['Kids', 'Young', 'Adult']:
        books = Book.objects.filter(book_agegroup__iexact=category)
    else:
        books = Book.objects.filter(book_category__iexact=category)

    context = {
        'books': books,
        'category': category
    }

    return render(request, 'readingapp/category_books.html', context)



def delete_book(request,id):
    book = Book.objects.get(id=id)
    book.delete()
    return redirect('/addbook/')
def deletebook(request, id):
    query= Book.objects.get(id=id)
    query.delete()
    return redirect('/addbook')

def login(request):
    if request.method=="POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        user=User.objects.filter(username= username)
        if user.exists():
            return redirect('/register')
        user = User.objects.create(
        
            username = username,
            email = email 
        )
        user.set_password(password)
        user.save()
        messages.info(request, 'Account Created Successfully')
        return redirect('/register')

    return render(request,"readingapp/register.html")    
# from django.contrib.auth import authenticate, login ,logout
def login1(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user) 
            return redirect('/addbook') # This line should work fine now
            # Redirect to a success page
        else:
            # Return an 'invalid login' error message.
            messages.error(request,'User does not exists')
            return redirect('/firstpage')  
    return render(request,"readingapp/login.html") 
def logout1(request):
    logout(request)
    return redirect('/login')
def vision(request):
    request.method=="POST" in request.POST
    return render(request,"readingapp/vision.html") 
def blog(request):
    request.method=="POST" in request.POST
    return render(request,"readingapp/blog.html") 
def volunteer(request):
    request.method=="POST" in request.POST
    return render(request,"readingapp/volunteer.html") 
def tc(request):
    request.method=="POST" in request.POST
    return render(request,"readingapp/T&C.html")
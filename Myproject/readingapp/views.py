from django.shortcuts import render, redirect
from .models import Book
from django.http import JsonResponse
from django.contrib import messages

from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
 
from django.contrib.auth import authenticate, login as auth_login, logout
import re
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen
# Create your views here.

  

def fetch_book_api_results(query, max_results=6):
    if not query:
        return []

    api_url = "https://openlibrary.org/search.json?" + urlencode({'q': query, 'limit': max_results})
    try:
        request = Request(api_url, headers={'User-Agent': 'BookClub/1.0'})
        with urlopen(request, timeout=8) as response:
            data = json.load(response)
    except Exception:
        return []

    results = []
    for doc in data.get('docs', [])[:max_results]:
        title = doc.get('title') or 'Unknown Title'
        author_list = doc.get('author_name', [])
        author = ' & '.join(author_list) if author_list else 'Unknown Author'
        cover_id = doc.get('cover_i')
        cover = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else None
        results.append({
            'title': title,
            'author': author,
            'year': doc.get('first_publish_year'),
            'cover': cover,
            'source': 'OpenLibrary',
        })
    return results


def homepage(request):
    search_query = request.GET.get('search', '').strip()
    queryset = Book.objects.all().order_by('-id')

    if search_query:
        queryset = queryset.filter(
            book_name__icontains=search_query
        )

    queryset = queryset[:6].values()
    api_results = fetch_book_api_results(search_query) if search_query else []

    context = {
        'viewbook': queryset,
        'api_results': api_results,
        'search_query': search_query,
    }
    return render(request, 'readingapp/homepage.html', context)

   
def show(request):
    user = Book.objects.all().values()
    return render(request, "readingapp/bookdata.html", {'users': user})


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


def deletebook(request, id):
    query = Book.objects.get(id=id)
    query.delete()
    return redirect('/addbook')
    query= Book.objects.get(id=id)
    query.delete()
    return redirect('/addbook')


def get_word_meaning(word, lang='en'):
    dictionary = {
        'ephemeral': {'en': 'lasting for a very short time', 'hi': 'क्षणिक'},
        'ubiquitous': {'en': 'found everywhere', 'hi': 'सर्वव्यापी'},
        'quaint': {'en': 'charmingly old-fashioned', 'hi': 'मनोरम'},
        'intricate': {'en': 'very complicated or detailed', 'hi': 'जटिल'},
        'ambiguous': {'en': 'open to more than one interpretation', 'hi': 'अस्पष्ट'},
        'eloquent': {'en': 'expressing yourself clearly and effectively', 'hi': 'बोली में प्रगतिशील'},
        'candid': {'en': 'honest and straightforward', 'hi': 'ईमानदार'},
    }
    return dictionary.get(word.lower(), {}).get(lang)


def generate_chat_response(query, image_file=None):
    query_text = query.strip().lower() if query else ''

    if image_file:
        info_parts = []
        info_parts.append(f"I received your image: {image_file.name}.")
        if hasattr(image_file, 'size'):
            info_parts.append(f"Image size: {image_file.size} bytes.")
        if 'cover' in query_text or 'book' in query_text or 'describe' in query_text:
            info_parts.append("I can help describe it by name or explain what you want from the image.")
        else:
            info_parts.append("Ask me questions like 'Describe this image' or 'What is this cover about?'")
        return ' '.join(info_parts)

    if 'summary' in query_text:
        title_match = re.search(r'summary of ([\w\s]+)', query_text)
        if title_match:
            title = title_match.group(1).strip()
            book = Book.objects.filter(book_name__icontains=title).first()
            if book:
                return (
                    f"Summary of '{book.book_name}' by {book.author_name}: "
                    f"This {book.book_category} book has {book.book_pages} pages and {book.book_chapter} chapters. "
                    f"It is ideal for {book.book_agegroup or 'all readers'} and explores themes common to {book.book_category} literature."
                )
            return "I couldn't find that book in the library. Please provide a more specific title or try another book."
        return "Please tell me which book you want a summary for, for example: 'Summary of Pride and Prejudice'."

    if 'recommend' in query_text or 'suggest' in query_text:
        category = None
        if 'mystery' in query_text:
            category = 'Mystery'
        elif 'romantic' in query_text or 'love' in query_text:
            category = 'Romantic'
        elif 'spiritual' in query_text or 'inspiration' in query_text:
            category = 'Spiritual'
        elif 'fiction' in query_text:
            category = 'Fiction'
        elif 'adventure' in query_text or 'travel' in query_text:
            category = 'Adventure'
        elif 'classic' in query_text:
            category = 'Classic'

        queryset = Book.objects.all()
        if category:
            queryset = queryset.filter(book_category__iexact=category)

        if queryset.exists():
            suggestions = queryset[:3]
            response_lines = ["Here are some books you may like:"]
            for book in suggestions:
                response_lines.append(f"{book.book_name} by {book.author_name} ({book.book_category})")
            return ' '.join(response_lines)
        return "I couldn't find a matching book recommendation right now. Try a different category or describe what you're looking for."

    if 'meaning' in query_text or 'translate' in query_text:
        lang = 'en'
        if 'hindi' in query_text:
            lang = 'hi'
        word_match = re.search(r'meaning of ([a-zA-Z]+)', query_text)
        if not word_match:
            word_match = re.search(r'translate ([a-zA-Z]+)', query_text)
        if word_match:
            word = word_match.group(1)
            meaning = get_word_meaning(word, lang)
            if meaning:
                return f"The meaning of '{word}' in {'Hindi' if lang=='hi' else 'English'} is: {meaning}."
            return f"I don't have the exact meaning for '{word}' yet, but I can help with other words."
        return "Please ask like 'Meaning of ephemeral in Hindi' or 'Translate ubiquitous'."

    return (
        "I can help with book summaries, recommendations, word meanings, or image details. "
        "Try asking: 'Recommend a mystery book', 'Summary of The Alchemist', "
        "or 'Meaning of intricate in Hindi'."
    )


def chat(request):
    if request.method == 'POST':
        query = request.POST.get('query', '').strip()
        image_file = request.FILES.get('image')
        response_text = generate_chat_response(query, image_file)
        return JsonResponse({'response': response_text})
    return redirect('/')


def login(request):
    if request.method == "POST":
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        if not username or not email or not password:
            messages.error(request, 'Please fill in all fields.')
            return render(request, 'readingapp/register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists. Please choose another or login.')
            return render(request, 'readingapp/register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email is already registered. Please login instead.')
            return render(request, 'readingapp/register.html')

        user = User.objects.create_user(username=username, email=email, password=password)
        auth_login(request, user)
        messages.success(request, 'Account created and logged in successfully.')
        return redirect('/addbook')

    return render(request, 'readingapp/register.html')

# from django.contrib.auth import authenticate, login ,logout
def login1(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('/addbook')
        messages.error(request, 'Invalid username or password.')
        return render(request, 'readingapp/login.html')

    return render(request, 'readingapp/login.html')

def logout1(request):
    logout(request)
    return redirect('/login')
def vision(request):
    return render(request, "readingapp/vision.html")

def blog(request):
    return render(request, "readingapp/blog.html")

def volunteer(request):
    return render(request, "readingapp/volunteer.html")

def tc(request):
    return render(request, "readingapp/T&C.html")
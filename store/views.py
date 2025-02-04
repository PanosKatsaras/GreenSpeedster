from django.shortcuts import render, get_object_or_404, redirect
from carts.views import _cart_id
from carts.models import CartItem
from .models import Product, ReviewRating ,About_Us
from category.models import Category
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from .forms import ReviewForm
from django.contrib import messages
from orders.models import OrderProduct
from .forms import ContactForm
from django.core.mail import send_mail
from django.template.loader import render_to_string
# Create your views here.


def store(request, category_slug=None):
    categories = None
    products = None

    if category_slug != None:
        categories = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(
            category=categories, is_available=True)
        paginator = Paginator(products, 3)
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)
        product_count = products.count()
    else:
        products = Product.objects.all().filter(is_available=True).order_by('id')
        paginator = Paginator(products, 6)
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)
        product_count = products.count()

    context = {
        'products': paged_products,
        'product_count': product_count,
    }
    return render(request, 'store/store.html', context)


def product_detail(request, category_slug, product_slug):
    try:
        single_product = Product.objects.get(
            category__slug=category_slug, slug=product_slug)
        in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(
            request), product=single_product).exists()
    except Exception as e:
        raise e
    
    if request.user.is_authenticated:
        try:
            orderproduct = OrderProduct.objects.filter(user=request.user, product_id=single_product.id).exists()
        except OrderProduct.DoesNotExist:
            orderproduct = None
    else:
        orderproduct = None
    #Get the reviews
    reviews = ReviewRating.objects.filter(product_id=single_product.id, status=True)

    context = {
        'single_product': single_product,
        'in_cart': in_cart,
        'orderproduct': orderproduct,
        'reviews': reviews,
    }
    return render(request, 'store/product_detail.html', context)


def search(request):
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            products = Product.objects.order_by('-created_date').filter(
                Q(description__icontains=keyword) | Q(product_name__icontains=keyword))
            product_count = products.count()
    context = {
        'products': products,
        'product_count': product_count,
    }
    return render(request, 'store/store.html', context)

def search_price(request):
    if request.method == "GET":   
        min_price = request.GET['min_price']
        max_price = request.GET['max_price']
        if min_price == '' and max_price== '':
            min_price = 0
            max_price = 15000
        elif min_price == '':
            min_price = 0
        elif max_price == '':
            max_price = 15000 
        products = Product.objects.filter(Q(price__gte=min_price) & Q(price__lte=max_price))
        product_count = products.count()   
        context = {
            'min_price': min_price,
            'max_price': max_price,
            'product_count': product_count, 
            'products' : products,  
        }

        return render(request, 'store/store.html', context)


def submit_review(request, product_id):
    url = request.META.get('HTTP_REFERER') # Store the product_detailed item url for redirection 
    if request.method == 'POST':
        try:
            #Check if review exists based of user id
            reviews = ReviewRating.objects.get(user__id=request.user.id, product__id=product_id)
            form = ReviewForm(request.POST, instance=reviews) # Passing the instance in order to update curent users review if exists
            form.save()
            messages.success(request, 'Thank you! Your review has been updated.')
            return redirect(url)
        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)
            if form.is_valid():
                # Cleaning the form data
                data = ReviewRating()
                data.subject = form.cleaned_data['subject']
                data.rating = form.cleaned_data['rating']
                data.review = form.cleaned_data['review']
                data.ip = request.META.get('REMOTE_ADDR')
                data.product_id = product_id
                data.user_id = request.user.id
                data.save()
                messages.success(request, 'Thank you! Your review has been submitted.')
                return redirect(url)

def terms(request):
    return render(request, "store/terms.html")



def about_us(request):

    About_Usdata = About_Us.objects.all()

    context = {
        'About_Us': About_Usdata,
    }
    return render(request,'Company/About_Us.html', context)

def service(request):
    return render(request,'Company/Service.html')

def returns_refunds(request):
    return render(request,'Company/Returns_Refunds.html')

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            content = form.cleaned_data['content']

            html = render_to_string('store/contact_message.html',{
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'content': content
            })
            send_mail('subject:','Thank you for your message!','',['greenspeedster_gr@hotmail.com'],html_message=html)
            return redirect('contact')
    else:
        form = ContactForm()
        context = {
            'form': form,
        }
    return render(request, 'store/contact.html', context)
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
# ...existing imports...

@login_required
def add_product(request):
    if request.method == 'POST':
        # ...existing code for processing POST requests...
        # Ensure the product is added to the database
        # ...existing code...
        return redirect('product_list')  # Redirect after successful POST
    elif request.method == 'GET':
        return render(request, 'addproduct.html')  # Render form for GET requests
    else:
        return HttpResponse(status=405)  # Method not allowed for other HTTP methods

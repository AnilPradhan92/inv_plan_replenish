from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

import json, os, subprocess, sys

from .models import Warehouse, ProductMaster
from .serializers import WarehouseSerializer, ProductMasterSerializer

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


@csrf_exempt
def login_user(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            username = data.get("username")
            password = data.get("password")

            user = authenticate(username=username, password=password)

            if user is not None:
                return JsonResponse({"success": True, "message": "Login successful"})
            else:
                return JsonResponse({"success": False, "message": "Invalid credentials"}, status=401)
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=500)
    else:
        return JsonResponse({"message": "Only POST method allowed"}, status=405)

@csrf_exempt
@api_view(['GET', 'POST'])
def warehouse_list_create(request):
    if request.method == 'GET':
        warehouses = Warehouse.objects.all()
        serializer = WarehouseSerializer(warehouses, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = WarehouseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
@api_view(['PUT', 'DELETE'])
def warehouse_update_delete(request, pk):
    try:
        warehouse = Warehouse.objects.get(pk=pk)
    except Warehouse.DoesNotExist:
        return Response({"error": "Warehouse not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PUT':
        serializer = WarehouseSerializer(warehouse, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        warehouse.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
def upload_product_master(request):
    if not isinstance(request.data, list):
        return Response({"error": "Expected a list of product entries."}, status=400)

    new_count = 0
    updated_count = 0
    for item in request.data:
        sku = item.get("sku")
        if not sku:
            continue
        obj, created = ProductMaster.objects.update_or_create(
            sku=sku,
            defaults=item
        )
        if created:
            new_count += 1
        else:
            updated_count += 1

    return Response({
        "message": "Upload successful",
        "new_skus": new_count,
        "updated_skus": updated_count
    }, status=201)

@api_view(['GET'])
def get_product_master(request):
    products = ProductMaster.objects.all()
    serializer = ProductMasterSerializer(products, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_data_sources_status(request):
    def get_max_date(table, column):
        with connection.cursor() as cursor:
            try:
                cursor.execute(f"SELECT MAX({column}) FROM {table}")
                row = cursor.fetchone()
                return row[0].strftime('%d-%b-%y') if row[0] else 'No data'
            except Exception as e:
                print(f"Error fetching from {table}: {e}")
                return f"Error: {str(e)}"

    return Response({
        "inventory": get_max_date("inventory_data", "report_date"),
        "sales": get_max_date("sales_data", "order_date"),
        "drr": "21-May-25",
        "replenishment": "21-May-25"
    })

@api_view(['POST'])
def trigger_sync(request, key):
    script_map = {
        'inventory': os.path.join(BASE_DIR, 'backend_scripts', 'download_inventory.py'),
        'sales': os.path.join(BASE_DIR, 'backend_scripts', 'download_sales.py'),
        'drr': os.path.join(BASE_DIR, 'backend_scripts', 'download_drr.py'),
        'replenishment': os.path.join(BASE_DIR, 'backend_scripts', 'download_replenishment.py'),
    }

    script_path = script_map.get(key)
    if not script_path:
        return Response({'error': 'Invalid key'}, status=400)

    try:
        result = subprocess.run(
            [sys.executable, script_path],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"{key} sync output:\n{result.stdout}")
        return Response({'message': f'{key} script executed successfully'})
    except subprocess.CalledProcessError as e:
        print(f"Script error for {key}:\n{e.stderr}")
        return Response({'error': f'{key} sync failed: {e.stderr}'}, status=500)

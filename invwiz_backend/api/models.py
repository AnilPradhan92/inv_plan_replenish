from django.db import models

class Warehouse(models.Model):
    name = models.CharField(max_length=100, unique=True)
    doh = models.PositiveIntegerField()
    max_inventory = models.PositiveIntegerField()

    def __str__(self):
        return self.name

class ProductMaster(models.Model):
    sku = models.CharField(max_length=100, unique=True)
    group1 = models.CharField(max_length=100, blank=True)
    sub_group1_1 = models.CharField(max_length=100, blank=True)
    drr = models.FloatField(default=0)
    required_doh = models.PositiveIntegerField(default=0)
    seasonality = models.CharField(max_length=50, blank=True)
    lifecycle_status = models.CharField(max_length=50, blank=True)
    current_inventory = models.IntegerField(default=0)
    grn_inventory = models.IntegerField(default=0)
    buffer_inventory = models.IntegerField(default=0)

    def __str__(self):
        return self.sku


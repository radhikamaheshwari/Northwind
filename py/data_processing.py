from pyspark import SparkContext, SparkConf
from pyspark.sql import SQLContext
from pyspark.sql.types import DoubleType, IntegerType,FloatType
from pyspark.sql.functions import udf

conf = SparkConf()\
    .setAppName("Data Processing for Emporio Analytics")\
    .set("spark.serializer", "org.apache.spark.serializer.KryoSerializer")

sc = SparkContext(conf=conf)
sqlContext =SQLContext(sc)

properties = {
    "url": "jdbc:mysql://relational.fit.cvut.cz:3306/northwind",
    "driver": "com.mysql.jdbc.Driver",
    "user":"guest",
    "password":"relational",
    "numPartitions":"1"
}

def main():

# ************* Will be joining the Datasets below to create a Denormalized Dataset --- DetailedOrders**************

    OrderDetailsDF = sqlContext.read.format("jdbc").options(
        **properties).options(dbtable="`Order Details`"
    ).load()

    OrdersDF = sqlContext.read.format("jdbc").options(
        **properties).options(dbtable="Orders"
    ).load()

    ShippersDF = sqlContext.read.format("jdbc").options(
        **properties).options(dbtable="Shippers"
    ).load()

# ************* Will be joining the Datasets below to create a Denormalized Dataset --- Customers**************


    CustomersDF = sqlContext.read.format("jdbc").options(
        **properties).options(dbtable="Customers"
    ).load()

    CustomerCustomerDemoDF = sqlContext.read.format("jdbc").options(
        **properties).options(dbtable="CustomerCustomerDemo"
    ).load()

    CustomerDemographicsDF = sqlContext.read.format("jdbc").options(
        **properties).options(dbtable="CustomerDemographics"
    ).load()


# ************* Will be joining the Datasets below to create a Denormalized Dataset --- Employees**************

    EmployeesDF = sqlContext.read.format("jdbc").options(
        **properties).options(dbtable="Employees"
    ).load()

    EmployeeTerritoriesDF = sqlContext.read.format("jdbc").options(
        **properties).options(dbtable="EmployeeTerritories"
    ).load()

    TerritoriesDF = sqlContext.read.format("jdbc").options(
        **properties).options(dbtable="Territories"
    ).load()
    
    RegionDF = sqlContext.read.format("jdbc").options(
        **properties).options(dbtable="Region"
    ).load()


# ************* Will be joining the Datasets below to create a Denormalized Dataset --- Products**************

    ProductsDF = sqlContext.read.format("jdbc").options(
        **properties).options(dbtable="Products"
    ).load()

    SuppliersDF = sqlContext.read.format("jdbc").options(
        **properties).options(dbtable="Suppliers"
    ).load()

    CategoriesDF = sqlContext.read.format("jdbc").options(
        **properties).options(dbtable="Categories"
    ).load()

# ************* Denormalizing the datasets ************

    DetailedOrdersDF = OrdersDF.join(OrderDetailsDF,
                                         (OrderDetailsDF.OrderID == OrdersDF.OrderID),
                                         'left').drop(OrderDetailsDF.OrderID
                                         ).join(ShippersDF,
                                                (OrdersDF.ShipVia == ShippersDF.ShipperID),
                                                'right').drop(OrdersDF.ShipVia)

    DetailedCustomersDF = CustomersDF.join(CustomerCustomerDemoDF,
                                           (CustomersDF.CustomerID == CustomerCustomerDemoDF.CustomerID),
                                           'left').drop(CustomerCustomerDemoDF.CustomerID
                                        ).join(CustomerDemographicsDF,
                                                (CustomerCustomerDemoDF.CustomerTypeID == CustomerDemographicsDF.CustomerTypeID),
                      
                         'right').drop(CustomerCustomerDemoDF.CustomerTypeID)

    DetailedEmployeesDF = EmployeesDF.join(EmployeeTerritoriesDF,
                                           (EmployeesDF.EmployeeID == EmployeeTerritoriesDF.EmployeeID),
                                           'left').drop(EmployeeTerritoriesDF.EmployeeID
                                        ).join(TerritoriesDF,
                                                (EmployeeTerritoriesDF.TerritoryID == TerritoriesDF.TerritoryID),
                                            'right').drop(EmployeeTerritoriesDF.TerritoryID)
                                         .join(RegionDF,TerritoriesDF.RegionID==RegionDF.RegionID,'right')
                                         .drop(TerritoriesDF.RegionID)

    DetailedProductsDF = SuppliersDF.join(ProductsDF,
                                         (ProductsDF.SupplierID == SuppliersDF.SupplierID),
                                         'left').drop(ProductsDF.SupplierID
                                        ).join(CategoriesDF,
                                                (ProductsDF.CategoryID == CategoriesDF.CategoryID),
                                            'right').drop(ProductsDF.CategoryID)

    #Adding another column "total_paid_price" in DetailedOrdersDF with formula: total_paid_price = UnitPrice * Quantity - Discount
    DetailedOrdersDF_tpp=DetailedOrdersDF.withColumn("total_paid_price",(DetailedOrdersDF['UnitPrice'].cast('double')*DetailedOrdersDF['Quantity'])-DetailedOrdersDF['Discount'])
    DetailedOrdersDF_tpp.registerTempTable('DetailedOrders')

    #Task-2 : Calculated Month from order date and doing a sum(total_paid_price), group by CustomerID,month

    sqlContext.sql('select CustomerID,month(OrderDate) as month,sum(total_paid_price) from DetailedOrders group by CustomerID,month').coalesce(2).write.csv("Task-2")

    #Task-3 : Counting distinct CustomerIDs from the DetailedOrders where total_price_paid by customer for that product is > 50

    sqlContext.sql('select ProductID,count(distinct CustomerID) from DetailedOrders where total_paid_price>=50 group by ProductID').coalesce(2).write.csv("Task-3")

    DetailedOrdersDF.write.csv("Task-1/DetailedOrders")
    DetailedCustomersDF.write.csv("Task-1/DetailedCustomers")
    DetailedEmployeesDF.write.csv("Task-1/DetailedEmployees")
    DetailedProductsDF.write.csv("Task-1/DetailedProducts")

if __name__ == '__main__':
    main()


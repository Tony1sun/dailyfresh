from django.contrib import admin

from goods.models import GoodsType, IndexPromotionBanner, IndexGoodsBanner, IndexTypeGoodsBanner

# Register your models here.
class BaseModelAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        '''新增或者更新表中的数据时调用'''
        super().save_model(request, obj, form, change)

        #发出任务,让celery worker重新生成首页静态页
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()

    def delete_model(self, request, obj):
        '''删除表中数据时调用'''
        super().delete_model(request, obj)
        #发出任务,让celery worker重新生成首页静态页
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()

class GoodsTypeAdmin(BaseModelAdmin):
    pass

class IndexGoodsBannerAdmin(BaseModelAdmin):
    pass

class IndexTypeGoodsBannerAdmin(BaseModelAdmin):
    pass

class IndexPromotionBannerAdmin(BaseModelAdmin):
    pass


admin.site.register(GoodsType, GoodsTypeAdmin)
admin.site.register(IndexGoodsBanner, IndexGoodsBannerAdmin)
admin.site.register(IndexTypeGoodsBanner, IndexTypeGoodsBannerAdmin)
admin.site.register(IndexPromotionBanner, IndexPromotionBannerAdmin)

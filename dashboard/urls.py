
from django.urls import path
from .views import DashboardStatsView, DashboardActivityFeedView

urlpatterns = [
    path('stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('activity/', DashboardActivityFeedView.as_view(), name='dashboard-activity'),
]

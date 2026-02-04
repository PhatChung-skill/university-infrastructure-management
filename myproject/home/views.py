from django.shortcuts import render
from django.views import View
from django.contrib.auth.views import LoginView
from .forms import BootstrapAuthenticationForm

class Login(LoginView):
    template_name = 'login.html'
    authentication_form = BootstrapAuthenticationForm

from django.core.serializers import serialize
from .models import Building, Tree, Incident, Equipment

def map_view(request):
    # 1. Lấy dữ liệu và chuyển sang GeoJSON
    # Chúng ta lấy các trường cần thiết để hiển thị Popup (name, description, status...)
    
    buildings_geojson = serialize('geojson', Building.objects.all(), 
                                  geometry_field='geom', 
                                  fields=('name', 'description'))
    
    trees_geojson = serialize('geojson', Tree.objects.all(), 
                              geometry_field='geom', 
                              fields=('code', 'species', 'health_status'))
    
    incidents_geojson = serialize('geojson', Incident.objects.all(), 
                                  geometry_field='geom', 
                                  fields=('title', 'status', 'priority'))

    # 2. Truyền dữ liệu sang template
    context = {
        'buildings_json': buildings_geojson,
        'trees_json': trees_geojson,
        'incidents_json': incidents_geojson,
    }
    return render(request, 'home/map.html', context)
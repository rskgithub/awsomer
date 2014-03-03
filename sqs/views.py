from django.shortcuts import render, redirect
from django.views.decorators.cache import cache_page
from .forms import *
from boto.exception import SQSError
import boto.sqs
from boto.sqs.message import Message

def connector(region='us-east-1'):
    conn = boto.sqs.connect_to_region(region)
    return conn

def queues(request):
    conn = connector()
    if request.POST:
        form = AddQueueForm(request.POST)
        if form.is_valid():
            conn.create_queue(form.cleaned_data['name'])
            return redirect('/sqs/queue/' + form.cleaned_data['name'])
    queues = []
    ques = conn.get_all_queues()
    for que in ques:
        item = {}
        item['name'] = que.name 
        try:
            item['attrib'] = que.get_attributes()
        except SQSError:
            pass
        queues.append(item)

    form = AddQueueForm()
    return render(request, 'sqs/queues.html', {
            'form': form,
            'queues': queues
        })  

def queue(request, queue_name):
    conn = connector()
    queue = conn.get_all_queues(prefix=queue_name)[0]
    if request.POST:
        if '_clear' in request.POST:
            queue.clear()
            return redirect('/sqs/queue/' + queue_name)
        # will have to wait for s3 integration
        #if '_dump' in request.POST:
        #    queue.save_to_s3('sqs_dump')
        elif '_delete' in request.POST:
            queue.delete()
            return redirect('/sqs/queue/')
        form = AddMessageForm(request.POST)
        if form.is_valid():
            m = Message()
            m.set_body(form.cleaned_data['message']) 
            count = form.cleaned_data['count']
            while count: 
                queue.write(m)
                count -= 1
            return redirect('/sqs/queue/' + queue_name)
    else:
        form = AddMessageForm()

    item = queue.get_attributes()
    item['name'] = queue.name

    return render(request, 'sqs/queue.html', {
            'queue': item,
            'form': form,
        })  


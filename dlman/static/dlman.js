function humanFileSize(size) {
    var i = Math.floor( Math.log(size) / Math.log(1024) );
    return ( size / Math.pow(1024, i) ).toFixed(2) * 1 + ' ' + ['B', 'kB', 'MB', 'GB', 'TB'][i];
};
$('#add-button').on('click', function() {
    var url = $('#url').val();
    $.post(URLS['add'], {'url': url});
    $('#url').val("");
});

class Download {
    constructor(data) {
        this.update(data, true);
        this.element = $('#download-template').contents().clone();
        this.element.find('#placeholder').attr('id', this.id);
        this.element.find('.download-title').text(this.name);
        this.element.find('.download-size').text(humanFileSize(this.size));
        this.element.find('.download-complete').text(humanFileSize(this.complete));
        this.element.find('.download-cancel').on('click', this.cancel.bind(this));
        this.element.find('.download-remove').on('click', this.remove.bind(this));
        $('#download-list').append(this.element);
        this.updateUI();
    }

    update(data, initial=false) {
        this.name = data['name'];
        this.size = data['size'];
        this.complete = data['complete'];
        this.id = data['id'];
        this.failed = data['failed'];
        this.finished = data['finished'];
        if (!initial) {
            this.updateUI()
        }
    }

    updateUI() {
        var percent = (this.complete / this.size) * 100
        var rounded = percent.toFixed(1)
        this.element.find('.download-complete').text(humanFileSize(this.complete));
        var bar = this.element.find('.download-bar')
        bar.css("width", percent + "%").text(rounded + "%");
        bar.attr("aria-valuenow", rounded);
        if (this.finished || this.failed) {
            this.element.find('.download-cancel').attr('disabled', true);
            bar.removeClass(['progress-bar-striped', 'progress-bar-animated'])
        } else {
            bar.removeClass(['bg-success', 'bg-danger'])
            this.element.find('.download-cancel').attr('disabled', false);
        }
        if (this.finished) {
            bar.addClass('bg-success');
        } else if (this.failed) {
            bar.addClass('bg-danger');
        } else {
            bar.addClass(['progress-bar-striped', 'progress-bar-animated']);
        }
    }

    remove() {
        $.post(URLS['remove'], {'id': this.id}, 'json');
    }

    destroy() {
        this.element.remove()
    }

    cancel() {
        $.post(URLS['cancel'], {'id': this.id}, 'json');
    }
}

class DownloadManager {
    constructor() {
        this.downloads = {};
        this.events = new EventSource(URLS['sse']);
        this.events.addEventListener("update", this.update.bind(this));
        this.events.addEventListener("remove", this.remove.bind(this));
        this.events.addEventListener("add", this.add.bind(this));
        this.resync()
    }
    
    resync() {
        for (var member in this.downloads) {
            delete this.downloads[member];
        }
        $.getJSON(URLS['status'], function(data) {
            data.forEach(this.addDownload.bind(this));
        }.bind(this));
    }

    addDownload(element) {
        this.downloads[element.id] = new Download(element);
    }

    processEvent(event, func) {
        var data = JSON.parse(event.data);
        data.forEach(function(element) {
            if (element.id in this.downloads) {
                func(this.downloads[element.id], element);
            };
        }.bind(this));
    }

    remove(event) {
        this.processEvent(event, function(download, element) {
            download.destroy();
            delete this.downloads[element.id];
        }.bind(this))
    }
    add(event) {
        var data = JSON.parse(event.data);
        data.forEach(function(element) {
            this.addDownload(element);
        }.bind(this));
    }
    update(event) {
        this.processEvent(event, function(download, element) {
            download.update(element)
        })
    }
}
dm = new DownloadManager();
function [ counts, ml_analyzed, times, classes ] = read_class_summary( filename )
% read a JSON class summary file (which must contain a ml_analyzed field)
% requires MATLAB R2016b or later.

% read and decode JSON
j = jsondecode(fileread(filename));

% these are usable as-is
classes = j.classes;
ml_analyzed = j.ml_analyzed;

% convert text timestamps to datenums
times = datenum(datetime(j.timestamps,'InputFormat','yyyy-MM-dd HH:mm:ss'));

% convert counts structure to 2d array
counts = zeros(length(times), length(classes));

for i=1:length(classes)
    counts(:,i) = j.counts.(classes{i});
end

% sort everything by time
[times, sort_idx] = sort(times);
counts = counts(sort_idx,:);
ml_analyzed = ml_analyzed(sort_idx);

end
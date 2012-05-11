#require 'warbler'
#Warbler::Task.new

require 'rake'
require 'rspec/core/rake_task'

desc 'Default: run specs'
task :default => :spec


desc 'Specs'
RSpec::Core::RakeTask.new(:spec) do |t|
  t.pattern = './spec/**/*_spec.rb' # don't need this, it's default
  t.verbose = true
  #t.rspec_opts = "--format documentation --color"
  # Put spec opts in a file named .rspec in root
end

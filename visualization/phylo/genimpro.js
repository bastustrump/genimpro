
    var color = d3.scaleOrdinal(d3.schemeCategory20);
    var geneColor = d3.scaleOrdinal(d3.schemeCategory20b);
    var hpcScale = ['A', 'A#', 'B', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#'];
    var currentGraph = {},
        fullGraph = {};
    var margin = {
        top: 10,
        right: 20,
        bottom: 10,
        left: 10
    };

    var audio = document.getElementById('audioElement');
    var soundcellAudio = document.getElementById('soundcellAudio');

    var AlignActivated = false;

    var svg = d3.select("#soundcellsVis"),
        width = +svg.attr("width"),
        height = +svg.attr("height"),
        radius = 7;


    var currentTime = svg.append("g")
        .attr("class", "currentTime")
        .append("line")
        .style("opacity", 0);

    var soundcellVis = svg.append("g");




    var maxDuration,maxDistance;

    var alphaTarget = 0.7;

    var x = d3.scaleTime(); //.range([margin.left, width-margin.right]);

    var soundcellsData, genome = {};

    var axisHeight = 35;
    var xAxis = d3.axisBottom(x)
        .tickFormat(d3.timeFormat("%M:%S"));

    var xAxisVis = svg.append("g")
        .attr("class", "axis")
        .attr("transform", "translate(0," + (height - 100) + ")")
        .style("opacity", "0")
        .call(xAxis);


    //Forces
    var forceX = d3.forceX(function(d) {
        return x(d.startTime);
    }).strength(function(d) {
        return 0.8;
    });

    var forceY = d3.forceY(function(d) {

        maxHeight = height - axisHeight;
        lineageHeight = 3.1 * radius;

        if (d.group == 1) {
            lineage = maxLineages - d.lineage;
            baseline = maxHeight / 2 - maxLineages * lineageHeight - lineageHeight / 2 - 0.15 * maxHeight; //4*lineageHeight;
        } else {
            baseline = maxHeight / 2 - (maxLineages * lineageHeight) / 2 + 0.15 * maxHeight;
            lineage = d.lineage;
        }
        shift = lineage * lineageHeight;
        return baseline + shift;
    });

    var forceCharge = d3.forceManyBody();
        // .distanceMax(100)
        // .distanceMin(20)
        // .strength(function(d) {
        //     return -150;
        // });

    var forceCenter = d3.forceCenter(width / 2, height / 2);

    var simulation = d3.forceSimulation()
        .force("link", d3.forceLink().id(function(d) {
            return d.id;
        }));


    $('#collapseOne').on('hidden.bs.collapse', function() {
        updateDimensions();
    })

    $('#collapseOne').on('shown.bs.collapse', function() {
        updateDimensions();
    })

    $("#recordingSelector").on("click", "li", function(event) {
        var recordingID = d3.select(this).attr("recordingID");
        $("#recordingButton").html($(this).find('a').text() + ' <span class="caret"></span>');
        loadRecording(recordingID);

        $.get("http://0.0.0.0:8080/audioForRecording/" + recordingID, function(data) {
            var element;
            if (data.substring(0, 6) == "<audio") {
                element = data.substring(27, data.length - 8);
            } else {
                element = data;
            }

            $("#audioElement").html(element);
            $("#audioElement").load();

        });

    })


    d3.json("http://0.0.0.0:8080/recordings", function(error, recordings) {

        var recordingSelector = d3.select("#recordingSelector");
        //recordings = recordings.slice(150, 260);
        var recordingLi = recordingSelector.selectAll("li").data(recordings);

        recordingLi.attr("recordingID", function(d, i) {
                return recordings[i]["ID"];
            })
            .attr("role", "presentation");

        recordingLi.exit().remove();
        recordingLi.enter().append("li")
            .attr("recordingID", function(d, i) {
                return recordings[i]["ID"];
            })
            .append("a")
            .attr("role", "menuitem")
            .attr("tabindex", "-1")
            .attr("href", "#")
            .text(function(d, i) {
                return "Recording: " + recordings[i]["ID"];
            });

        $('#recordingButton').removeClass('disabled');
        $('#recordingButton').parent().removeClass('disabled');
    });


    $(window).keyup(function(e) {
        if (e.keyCode === 32) {
            if (audio.paused == true)
                audio.play();
            else
                audio.pause();
        }
    });

    audio.addEventListener("timeupdate", function(e) {
        currentTime //.transition().duration(10)
            .attr("x1", function(d) {
                return x(new Date(+audio.currentTime * 1000));
            })
            .attr("y1", function(d) {
                return 0;
            })
            .attr("x2", function(d) {
                return x(new Date(+audio.currentTime * 1000));
            })
            .attr("y2", function(d) {
                return height - axisHeight - 30;
            });

        partGraph(audio.currentTime);
    }, false);

    // audio.addEventListener("playing", function(e){
    //   if (AlignActivated) {
    //     currentTime.transition().duration(100).style("opacity", 1);
    //   }
    // });

    // audio.addEventListener("pause", function(e){
    //   currentTime.transition().duration(100)
    //     .style("opacity", 0);
    // });



    simulation.force("link").strength(0.4)
        .distance(function(d) {

            if (d.distance) {
                //return 50.0 * d.distance;
                return 1.0 * radius +  45 * d.distance; // maxDistance);
            } else {
                return 30;
            }
        });

    simulation.force("charge", forceCharge)
        .force("center", forceCenter)
        .force("collide", d3.forceCollide(nodeRadius*0.8))
        .alphaTarget(alphaTarget)
        .on("tick", ticked);


    function toggleVis(toggleAlign) {

        if (!toggleAlign) {

            simulation.force("forceY", null);
            simulation.force("forceX", null);
            simulation.force("charge", forceCharge);
            simulation.force("center", forceCenter);
            simulation.force("link").strength(0.8);
            AlignActivated = false;

            currentTime.transition().duration(100).style("opacity", 0);

            xAxisVis.transition()
                .duration(150).style("opacity", "0");

        } else {

            simulation.force("link").strength(0.001);
            simulation.force("charge", null);
            simulation.force("center", null);
            simulation.force("forceY", forceY);
            simulation.force("forceX", forceX);

            simulation.force("forceX")
                .strength(function(d) {
                    return 0.9;
                });

            simulation.force("forceY")
                .strength(function(d) {
                    return 0.8;
                });

            xAxisVis.transition()
                .duration(550).style("opacity", "1");

            currentTime.transition().duration(100).style("opacity", 1);
            AlignActivated = true;
        }
    }



    function nodeRadius(d) {
        var nodeRadius = radius + 18.5 * d.duration / maxDuration;
        if (d.group == 1) {
            return nodeRadius - 2;
        } else {
            return nodeRadius;
        }
    }


    function loadRecording(recordingID) {
        d3.json("http://0.0.0.0:8080/genetics/" + recordingID, function(error, treeData) {
            toggleVis(false);
            fullGraph = treeData;
            loadGraph(fullGraph);
        });

        d3.json("http://0.0.0.0:8080/soundcells/" + recordingID, function(error, data) {
            soundcellsData = data;
            //console.log(soundcellsData);
            loadPhenotypeDomains();
        });

        d3.json("http://0.0.0.0:8080/genome", function(error, data) {
            genome["variants"] = data[0];
            genome["clusterGroups"] = data[1];
            //console.log(genome);
        });

    }

    function loadPhenotypeDomains() {
      var phenotypeValues = {};
      phenotypeChartKeys.forEach(function(key, i) {
        phenotypeValues[key] = soundcellsData.map(function(soundcell) {
            return soundcell.phenotype[key];
        });
        phenotypeDomains[key] = [
          d3.min(phenotypeValues[key]),
          d3.max(phenotypeValues[key])
        ];
      });

    }

    function loadGraph(graph) {

        var lineages = graph.nodes.map(function(obj) {
            return obj.lineage;
        });
        maxLineages = Math.max(...lineages) + 1;

        graph.nodes.forEach(function(d) {
            d.endTime = new Date(+(d.startTime + d.duration) * 1000);
            d.startSeconds = d.startTime;
            d.startTime = new Date(+d.startTime * 1000);
        });

        maxDuration = d3.max(graph.nodes, function(d) {
            return d.duration;
        });

        maxDistance = d3.max(graph.links, function(d) {
            return d.distance;
        });

        x.domain([new Date(0), d3.max(graph.nodes, function(d) {
            return d.endTime;
        })]);

        currentGraph = graph; //jQuery.extend({}, graph);

        updateDimensions();
        update();

    }

    function partGraph(currentTimeSeconds) {
        var localComplete = jQuery.extend({}, fullGraph);
        //var localComplete = fullGraph.slice();
        var partNodes = [],
            partLinks = [];

        fullGraph.nodes.forEach(function(d) {
            if (d.startSeconds <= currentTimeSeconds) {
                partNodes.push(d);
            }
        });

        fullGraph.links.forEach(function(d) {
            if ((d.source.startSeconds <= currentTimeSeconds) && (d.target.startSeconds <= currentTimeSeconds)) {
                partLinks.push(d);
            }
        });

        // var partNodes = fullGraph.nodes.filter(function(d) {
        //     return d.startSeconds <= currentTimeSeconds;
        // });

        // var partLinks = fullGraph.links.filter(function(d) {
        //     return (d.source.startSeconds <= currentTimeSeconds) && (d.target.startSeconds <= currentTimeSeconds);
        // });


        currentGraph = {
            "links": partLinks,
            "nodes": partNodes
        };

        update();

    }

    var link = soundcellVis.append("g")
        .attr("class", "links")
        .selectAll("path");

    var node = soundcellVis.append("g")
        .attr("class", "nodes")
        .selectAll("circle");

    function update() {

        xAxisVis.call(xAxis)
            .selectAll("text")
            .style("text-anchor", "start")
            .style("fill", "white")
            .attr("dx", "0")
            .attr("dy", "1em");

        var t = d3.transition().duration(750);

        node = node.data(currentGraph.nodes);

        node.exit().transition().duration(150)
            .attr("r", 0)
            .remove();

        node = node.enter().append("g")
            .attr("class", "node")
            .append("circle").call(function(node) {
                node.transition().duration(100);
            })
            .merge(node)
            .attr("r", nodeRadius)
            .attr("fill", function(d) {
                if (d.group == 1) {
                    return 'rgb(20,20,20)';
                } else {
                    return color(d.lineage);
                }
            })
            .style("stroke", function(d) {
                if (d.group == 1) {
                    return color(d.lineage);
                } else {
                    return 'rgb(20,20,20)';
                }
            });

        node.on("mouseover", nodeMouseover)
            .on("mouseout", nodeMouseout)
            .on("click", nodeClick)
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));

        link = link.data(currentGraph.links);
        link.exit().remove();
        link = link.enter().append("path").merge(link);

        simulation.nodes(currentGraph.nodes);
        simulation.force("link").links(currentGraph.links);

        node.each(function(d) {
            d.connectedNodes = [d]
            link.each(function(l) {
                if (l.source.lineage == d.lineage || l.target.lineage == d.lineage) {
                    if ($.inArray(l.source, d.connectedNodes) == -1) {
                        d.connectedNodes.push(l.source);
                    }
                    if ($.inArray(l.target, d.connectedNodes) == -1) {
                        d.connectedNodes.push(l.target);
                    }
                }
            });
        });


        simulation.alpha(1).restart();

        // if (AlignActivated){
        //   simulation.force("forceY", forceY);
        //     simulation.force("forceX", forceX);
        // }
        //toggleVis(AlignActivated);
    }

    var phenotypeChartLine, phenotypeChart, phenotypeX, phenotypeY, phenotypeLine, phenotypeVis, phenotypeChartData;

    var phenotypeChartKeys = [
          'DynamicGlobalLoudness',
          'DynamicSpread',
          'DynamicComplexity',
          'DynamicSkewness',
          'DynamicKurtosis',
          'Density',
          'FollowingRest',
          'RhythmicComplexity',
          'RhythmicFlatness',
          'RhythmicTempo',
          'RhythmicStability',
          'RhythmicUniformity',
          'HarmonicSpread',
          'MelodicComplexity',
          'MelodicSpread',
          'MelodicShape',
          'SpectralCentroid',
          'SpectralInharmonicity',
          'SpectralRoughness',
          'SpectralKurtosis',
          'SpectralFlux',
          'ZeroCrossingRate',
          'Detuning'];

    var phenotypeDomains = {};

    var hpcpKeys = ['HPCP 0', 'HPCP 1', 'HPCP 2', 'HPCP 3', 'HPCP 4', 'HPCP 5', 'HPCP 6', 'HPCP 7', 'HPCP 8', 'HPCP 9', 'HPCP 10', 'HPCP 11'];
    var intervalKeys = ['Interval 0', 'Interval 1', 'Interval 2', 'Interval 3', 'Interval 4', 'Interval 5', 'Interval 6', 'Interval 7', 'Interval 8', 'Interval 9', 'Interval 10', 'Interval 11'];


    function nodeClick(n) {

        d3.select(this).transition().duration(100)
            .attr("fill", function(d) {
                if (d.group == 1) {
                    return 'rgb(255,255,255)';
                } else {
                    return color(d.lineage);
                }
            })
            .style("stroke", function(d) {
                if (d.group == 1) {
                    return color(d.lineage);
                } else {
                    return 'rgb(255,255,255)';
                }
            });

        d3.selectAll(".node").selectAll("circle")
            .each(function(d) {
                if (d != n) {
                    d3.select(this)
                        .attr("fill", function(d) {
                            if (d.group == 1) {
                                return 'rgb(20,20,20)';
                            } else {
                                return color(d.lineage);
                            }
                        })
                        .style("stroke", function(d) {
                            if (d.group == 1) {
                                return color(d.lineage);
                            } else {
                                return 'rgb(20,20,20)';
                            }
                        });
                }
            });

        loadSelectedNode(n);
        phenotypeChartData = [];
        // for (var key in phenotypeChartKeys) {
        //     if (selectedNodeData.phenotype.hasOwnProperty(key)) {
        //         phenotypeChartData.push(selectedNodeData.phenotype[key]);
        //     }
        // }

        phenotypeChartKeys.forEach(function(d, i) {
          if (selectedNodeData.phenotype.hasOwnProperty(d)) {
              phenotypeChartData.push(relativeValueForKey(selectedNodeData.phenotype[d],d));
          }
        });
        console.log(selectedNodeData);
        updateSoundcellInspector();

    }

    function relativeValueForKey(value,key) {
      var scale = d3.scaleLinear().range([0, 1]);
      scale.domain(phenotypeDomains[key]);
      return scale(value);

    }

    setupSoundcellInspector();

    var phenotypeBarX;

    function setupSoundcellInspector() {
        phenotypeChart = d3.select("#phenotypeChart"),
            margin = {
                top: 20,
                right: 20,
                bottom: 50,
                left: 00
            },
            width = +phenotypeChart.attr("width") - margin.left - margin.right,
            height = +phenotypeChart.attr("height") - margin.top - margin.bottom,
            phenotypeVis = phenotypeChart.append("g").attr("transform", "translate(" + margin.left + "," + margin.top + ")");

        phenotypeBarX = d3.scaleBand().padding(0.1)
          .range([0, width])
          .domain(phenotypeChartKeys);

        // phenotypeX = d3.scaleLinear().rangeRound([0, width]);
        phenotypeY = d3.scaleLinear().rangeRound([height, 0]);
        //
        // phenotypeLine = d3.line()
        //     .x(function(d, i) {
        //         return phenotypeX(i);
        //     })
        //     .y(function(d, i) {
        //         return phenotypeY(d);
        //     });
        //
        // phenotypeX.domain([0, 10]);
        phenotypeY.domain([0, 1]);

        // phenotypeVis.append("g")
        //     .attr("class", "axis axis---x")
        //     .attr("transform", "translate(0," + height + ")")
        //     .call(d3.axisBottom(phenotypeBarX))
        //     .selectAll("text")
        //       .style("text-anchor", "end")
        //       .attr("dx", "-.8em")
        //       .attr("dy", ".15em")
        //       .attr("transform", "rotate(-65)");

        // phenotypeVis.append("g")
        //     .attr("class", "axis axis--y")
        //     .call(d3.axisLeft(phenotypeY));

    }


    function updateSoundcellInspector() {

        $.get("http://0.0.0.0:8080/soundcellAudio/" + selectedNodeData.ID, function(data) {
            var element;
            if (data.substring(0, 6) == "<audio") {
                element = data.substring(27, data.length - 8);
            } else {
                element = data;
            }

            $("#soundcellAudio").html(element);
            $("#soundcellAudio").load();

        });

        var hpcp = "&nbsp;";
        var intervals = "&nbsp;";

        hpcpKeys.forEach(function(d, i) {
          if (selectedNodeData.phenotype[d]==1) {
              hpcp = hpcp +  " " + hpcScale[i];
          }
        });

        intervalKeys.forEach(function(d, i) {
          if (selectedNodeData.phenotype[d]==1) {
              intervals = intervals +  " " + i;
          }
        });

        d3.select("#HPCP").html(hpcp);
        d3.select("#MelodicRoot").html("&nbsp;" + hpcScale[selectedNodeData.phenotype["MelodicRoot"]]);
        d3.select("#Intervals").html(intervals);
        d3.select("#soundcellID").html(selectedNodeData.ID);

        drawPhenotypeChart();


    }


    function drawPhenotypeChart() {

      bars = phenotypeVis.selectAll(".bar")
          .data(phenotypeChartData);

      bars.exit().remove();

      bars.enter().append("rect")
          .attr("class", "bar")
          .attr("x", function(d,i) { return phenotypeBarX(phenotypeChartKeys[i]); })
          .attr("width", phenotypeBarX.bandwidth())
          .on("mouseover", phenotypeMouseover)
          .on("mouseout", phenotypeMouseout);

        phenotypeVis.selectAll(".bar")
          .transition().duration(100)
          .attr("y", function(d) { return phenotypeY(d); })
          .attr("height", function(d) { return height - phenotypeY(d); });
    }


    function phenotypeMouseover(m,i) {
      d3.select("#phenotypeKey").html(phenotypeChartKeys[i]);
      d3.select("#phenotypeValue").html(selectedNodeData.phenotype[phenotypeChartKeys[i]].toFixed(3));
      d3.select("#phenotypeDomain").html("[" + phenotypeDomains[phenotypeChartKeys[i]][0].toFixed(2) + " - " + phenotypeDomains[phenotypeChartKeys[i]][1].toFixed(2) + "]");
    }


    function phenotypeMouseout(m,i) {
      d3.select("#phenotypeKey").html("");
      d3.select("#phenotypeValue").html("");
      d3.select("#phenotypeDomain").html("");
    }

    var selectedNodeData;

    function loadSelectedNode(n) {

        soundcellsData.forEach(function(d, i) {
            if (d.ID == n.id) {
                selectedNodeData = d;
            }
        });

    }

    function nodeMouseover(m) {

        var lineage = m.lineage;

        d3.selectAll(".node").selectAll("circle")
            .each(function(d) {

                if ($.inArray(d, m.connectedNodes) > -1) {
                    d3.select(this).transition().duration(100).attr("opacity", 1.0);
                } else {
                    d3.select(this).transition().duration(100).attr("opacity", 0.1);
                }
            });

        d3.selectAll(".links").selectAll("path")
            .each(function(d) {

                if (d.source.lineage == lineage || d.target.lineage == lineage) {
                    d3.select(this).transition().duration(100).attr("opacity", 1.0);
                } else {
                    d3.select(this).transition().duration(100).attr("opacity", 0.2);
                }

            });
    }

    function nodeMouseout() {
        d3.selectAll(".node").selectAll("circle").transition().duration(250).attr("opacity", 1.0);
        d3.selectAll(".links").selectAll("path").transition().duration(250).attr("opacity", 1.0);
    }

    function updateDimensions() {

        width = window.innerWidth - margin.right;
        height = window.innerHeight - $('#soundcellsVis').offset().top - 10 - $('#inspector').height();

        svg
            .attr('width', width)
            .attr('height', height);


        x.range([margin.left, width - margin.right]);

        xAxisVis.call(xAxis)
            .attr("transform", "translate(0," + (height - axisHeight - margin.bottom) + ")");

        if (AlignActivated) {
            simulation.force("forceY", forceY);
            simulation.force("forceX", forceX);
        } else {
            simulation.force("center", d3.forceCenter(width / 2, height / 2));
        }

    }

    var line = d3.line()
        .curve(d3.curveBundle.beta(0.98));


    d3.select(window).on('resize.updatesvg', updateDimensions);
    updateDimensions();






    function ticked() {

        link.attr("d", function(d) {
            var s = [],
                t = [],
                m = [],
                dp1 = [],
                dp2 = [];

            s.x = Math.max(radius, Math.min(width - radius, d.source.x));
            s.y = Math.max(radius, Math.min(height - radius - axisHeight - 30, d.source.y));

            t.x = Math.max(radius, Math.min(width - radius, d.target.x));
            t.y = Math.max(radius, Math.min(height - radius - axisHeight - 30, d.target.y));

            m.x = s.x + (t.x - s.x) / 2;
            m.y = s.y + (t.y - s.y) / 2;

            dp1.x = s.x;
            dp1.y = (s.y + m.y) / 2;

            dp2.x = t.x;
            dp2.y = (t.y + m.y) / 2;

            if (!AlignActivated) {
                return line([
                    [s.x, s.y],
                    [t.x, t.y]
                ]);
            }

            return line([
                [s.x, s.y],
                [dp1.x, dp1.y],
                [m.x, m.y],
                [dp2.x, dp2.y],
                [t.x, t.y]
            ]);

            var dx = d.target.x - d.source.x,
                dy = d.target.y - d.source.y,
                dr = 2.5 * Math.sqrt(dx * dx + dy * dy);
            return "M" + d.source.x + "," + d.source.y + "A" + dr + "," + dr + " 0 0,1 " + d.target.x + "," + d.target.y;


        });



        //link.attr("d", line([[d.source.x,d.source.y],[dp1.x,dp1.y],[m.x,m.y],[dp2.x,dp2.y],[d.target.x,d.target.y]]));


        node.attr("cx", function(d) {
                return d.x = Math.max(radius, Math.min(width - radius, d.x));
            })
            .attr("cy", function(d) {
                return d.y = Math.max(radius, Math.min(height - radius - axisHeight - 30, d.y));
            });


        // node
        //     .attr("cx", function(d) { return d.x; })
        //     .attr("cy", function(d) { return d.y; });

        //  labels
        // .attr("dx", function(d) { return d.x + 20; })
        //    .attr("dy", function(d) { return d.y; });
    }


    function dragstarted(d) {
        if (!AlignActivated) {
            if (!d3.event.active) simulation.alphaTarget(0.4).restart();
            d.fx = d.x;
            d.fy = d.y;
        }
    }

    function dragged(d) {
        if (!AlignActivated) {
            d.fx = d3.event.x;
            d.fy = d3.event.y;
        }
    }

    function dragended(d) {
        if (!AlignActivated) {
            if (!d3.event.active) simulation.alphaTarget(alphaTarget);
            d.fx = null;
            d.fy = null;
        }
    }
